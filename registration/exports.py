import json
from io import BytesIO

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from openpyxl import load_workbook
from openpyxl.styles import Font

from general_model import print_list
from registration.models import Registration, PlannedCourse
from studyguide.models import CourseType, MainCourse
from .CourseBrowser import CourseBrowser


def add_course_row(sheet, row, course, api=None, year=None, quartile=None):
    """
    Add a row with a course to an excel sheet

    :param sheet: OpenPyXL sheet
    :param row: row number
    :param course: course code
    :param api: api for coursebrowser. Use None for unknown course
    :return:
    """
    try:
        cb = api.get_course_data(course.Code)[0]
    except (ValueError, IndexError, TypeError):
        # code not known in coursebrowser.
        cb = {'name': 'Other',
              'ECTS': '?'}
    sheet['A{}'.format(row)].font = Font(bold=False, name='Calibri')
    sheet['B{}'.format(row)].font = Font(bold=False, name='Calibri')
    sheet['C{}'.format(row)].font = Font(bold=False, name='Calibri')

    sheet['A{}'.format(row)].value = "{} - {}".format(course.Code, cb['name'])
    sheet['B{}'.format(row)].value = "{} EC".format(cb['ECTS'])
    if isinstance(course, MainCourse):
        sheet['C{}'.format(row)].value = "Course is not planned."
    else:
        sheet['C{}'.format(row)].value = "Y{}Q{}".format(course.Year, course.Quartile)


def get_approval_xlsx():
    """
    Download excel file template from tue.nl

    :return: openpyxl workbook template
    """
    data = cache.get('approvalform.xlsx')
    if data is None:
        try:
            with open('proxies.json', 'r') as stream:
                proxies = json.loads(stream.readlines()[0].strip('\n'))
        except:
            proxies = {}
        try:
            r = requests.get(settings.APPROVAL_STUDY_PACKAGE_FORM_XLSX_LINK, headers={
                'User-Agent': 'MasterMarketplace by Kolibri Solutions',
                'From': 'mastermarketplace@tue.nl'
            }, proxies=proxies)
            if r.status_code != 200:
                raise Exception("Failed to download XLSX template from {}. (HTTP status code {})".format(settings.APPROVAL_STUDY_PACKAGE_FORM_XLSX_LINK, r.status_code))
        except Exception as e:
            raise Exception("Failed to download XLSX template from {}. (Exception {})".format(settings.APPROVAL_STUDY_PACKAGE_FORM_XLSX_LINK, e))

        data = r.content
        cache.set('approvalform.xlsx', data, 4 * 7 * 24 * 60 * 60)
    return load_workbook(BytesIO(data))


def get_approval_xlsx_filled(student):
    """
    Fill approval study package form xlsx sheet with data from student

    :param student:
    :return:
    """
    wb = get_approval_xlsx()
    sheet = wb.active
    try:
        reg = student.registration
        courseplanning = reg.courseplanning
    except Registration.DoesNotExist:
        raise PermissionDenied("Please fill in your registration and course planning first.")
    core_type = CourseType.objects.get(Name__iexact='Core Course')  # this name is set in init_populate
    prv_type = CourseType.objects.get(Name__iexact='Professional Development')  # this name is set in init_populate
    api = CourseBrowser()

    # fill in personal information
    sheet['B3'].value = student.usermeta.get_nice_name()
    sheet['B3'].font = Font(bold=False, name='Calibri')
    sheet['B4'].value = student.username
    sheet['B4'].font = Font(bold=False, name='Calibri')
    sheet['B5'].value = student.email
    sheet['B5'].font = Font(bold=False, name='Calibri')
    sheet['B6'].value = reg.Cohort
    sheet['B6'].font = Font(bold=False, name='Calibri')
    sheet['B7'].value = reg.get_Origin_display()
    sheet['B7'].font = Font(bold=False, name='Calibri')

    # TU/e Contacts
    sheet['B18'].value = print_list(reg.Program.Group.all().values_list('ShortName', flat=True))  # research group
    sheet['C18'].value = 'Specialization: {}'.format(reg.Program.Name)  # specialization path

    # Core Courses.
    core_codes = MainCourse.objects.filter(Type=core_type).values_list('Code', flat=True)
    core_codes_chosen = courseplanning.courses.filter(Code__in=core_codes)
    extra_rows = core_codes_chosen.count() - 3
    if extra_rows > 0:  # add extra rows if more than three courses
        for i in range(extra_rows):
            sheet.insert_rows(28)
    else:
        extra_rows = 0
    for i, course in enumerate(core_codes_chosen):
        add_course_row(sheet, 25 + i, course, api=api)

    # Professional skills.
    prv_codes = MainCourse.objects.filter(Type=prv_type).values_list('Code', flat=True)
    prv_codes_chosen = courseplanning.courses.filter(Code__in=prv_codes)
    extra_rows_prv = prv_codes_chosen.count() - 2
    if extra_rows_prv > 0:  # add extra rows if more than three courses
        for i in range(extra_rows_prv):
            sheet.insert_rows(34 + extra_rows)
    else:
        extra_rows_prv = 0
    for i, course in enumerate(prv_codes_chosen):
        add_course_row(sheet, 32 + extra_rows + i, course, api=api)
    extra_rows += extra_rows_prv  # shift worksheet down.

    # fill in specialization courses, always only 2 courses.
    scs = reg.Program.MainCourses.all()
    if len(scs) != 2:
        raise PermissionDenied("The number of main courses of this specialization path is invalid. Please contact support to correct the specialization path {}.".format(reg.Program))
    for i, course in enumerate(scs):
        try:  # see if course is planned.
            course = reg.courseplanning.courses.get(Code=course.Code)
            add_course_row(sheet, 37 + extra_rows + i, course, api)
        except PlannedCourse.DoesNotExist:  # or add default course
            add_course_row(sheet, 37 + extra_rows + i, course, api)

    # get all free electives
    free_codes_chosen = reg.courseplanning.courses.exclude(Code__in=prv_codes).exclude(Code__in=core_codes).exclude(Code__in=scs.values_list('Code', flat=True))  # to also include other uni/department codes.
    extra_rows_free = free_codes_chosen.count() - 6
    if extra_rows_free > 0:  # add extra rows if more than 6 courses
        for i in range(extra_rows_free):
            sheet.insert_rows(47 + extra_rows)
    for i, course in enumerate(free_codes_chosen):
        add_course_row(sheet, 42 + extra_rows + i, course, api=api)
    return wb
