from channels.consumer import SyncConsumer
from .models import CheckedUrl
from django.core.cache import cache
import json
import requests
from hashlib import sha256
from virustotal.secret import API_KEY
import time
from bs4 import BeautifulSoup
from general_mail import send_mail

import logging

logger = logging.getLogger('django')


class VirustotalProcess(SyncConsumer):
    method_mapping = {
        'virustotal.checklink': 'checklink',
    }

    def checklink(self, data):
        link = data.get('link')
        print("CHECKING LINK {}".format(link))
        if 'mailto' == link.split(':')[0]:
            # emails cant be virusscanned
            return

        logger.info("Virustotal called on link {}".format(link))
        h = sha256(link.encode()).hexdigest()
        report = cache.get('virustotal:' + h)

        if report is not None:
            return
        try:
            report = CheckedUrl.objects.get(URL=link)
            cache.set('virustotal:' + h, report, 24 * 60 * 60)
            return
        except CheckedUrl.DoesNotExist:
            pass

        cache.set('virustotal:' + h, 'working', 5 * 60)  # set an entry to show that this worker is busy with the link

        self.session = requests.session()
        try:
            with open('osiris/proxies.json', 'r') as stream:
                self.proxies = json.loads(stream.readlines()[0].strip('\n'))
        except:
            self.proxies = {}
        self.session.headers['User-Agent'] = 'Master Marketplace ELE Tue, master.ele.tue.nl'
        self.session.headers['From'] = 'mastermarketplace@tue.nl'
        self.session.headers['Accept-Encoding'] = "gzip, deflate"
        # talk to the virustotal API
        while True:
            logger.info("Virustotal report asked for link {}".format(link))
            r = self.session.post('https://www.virustotal.com/vtapi/v2/url/report', data={
                'apikey': API_KEY,
                'resource': link,
            }, timeout=30, proxies=self.proxies)
            if r.status_code != 200:  # if we are rate limited wait 15 seconds and try again
                time.sleep(15)
                continue
            data = r.json()
            try:
                if data['response_code'] != 1:  # if there is no report yet ask for a scan
                    scans = cache.get('virustotal:scans')
                    if scans is None:
                        scans = []
                    if h in scans:  # if link is already in scanning queue dont ask again to scan it
                        return
                    scans.append(h)
                    cache.set('virustotal:scans', scans, 24 * 60 * 60)
                    logger.info("Virustotal scan asked for link {}".format(link))
                    while True:
                        r = self.session.post('https://www.virustotal.com/vtapi/v2/url/scan', data={
                            'apikey': API_KEY,
                            'url': link,
                        }, timeout=30, proxies=self.proxies)

                        if r.status_code == 200:  # if we are rate limited wait 15 seconds and try again
                            break
                        else:
                            time.sleep(15)
                    return  # report will be read next time the link is queried
            except:
                return

            break
        logger.warning('Link {} scanned'.format(link))
        # scrape the report page to see http response code to check if target link is broken
        # this is not given in API
        r = self.session.get(data['permalink'], timeout=30, proxies=self.proxies)
        if r.status_code != 200:
            # report cannot be read so try again later
            return
        soup = BeautifulSoup(r.text, 'lxml')
        # find all child elements of the additional information part
        detailoptions = [e.text.lower() for e in soup.find('div', id='file-details').findChildren()]
        code = None
        for i, e in enumerate(detailoptions):
            # check where the http response code header starts
            if 'http response code' in e:
                # find the next number in elements which is the actual response code
                for ec in detailoptions[i:]:
                    try:
                        code = int(ec.strip('\n').strip())
                        break
                    except:
                        continue
                if code is not None:
                    break
        if code is None:
            code = 200
        # print("Response code: {}".format(code))
        # print("Positives: {}".format(data['positives']))
        report = CheckedUrl(URL=link)
        if code == 200 and data['positives'] == 0:
            report.Status = 1
        elif data['positives'] != 0:
            logger.warning('Link {} contains malware'.format(link))
            report.Status = 3
        elif code != 200:
            logger.warning('Link {} is broken'.format(link))
            report.Status = 2
        report.save()
        cache.set('virustotal:' + h, report, 24 * 60 * 60)
        if report.Status != 1:
            owner = cache.get('virustotal:owner:' + h)
            if owner is not None:
                send_mail('LinkGuard Notice', 'email/linkguardreport.html', {'url': report}, owner)
