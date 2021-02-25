# encoding=utf8
import time
import os
import subprocess
import hashlib
import binascii
import io
import shutil
import zipfile

from unidecode import unidecode

from pdfrw import PdfReader, PdfWriter

from youtube_transcript_api import YouTubeTranscriptApi
import requests


from django.shortcuts import redirect
from django.shortcuts import render
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.http import HttpResponse, Http404, JsonResponse, HttpResponseNotFound
from django.template import RequestContext


from PDFUpload import settings


#configs.py contains secrets that shouldn't be in the public repo
#so handle it if the file isn't there... don't prevent the whole app from running
try:
    from pdf_annotator.configs import CLIENT_ID, API_KEY, SCOPES  
except ImportError:
    CLIENT_ID = ''
    API_KEY = ''
    SCOPES = []

import sys
import os
import random, string
import re
import time

import os.path
from textwrap import TextWrapper
from docx import opendocx, getdocumenttext
from xtopdf.PDFWriter import PDFWriter

import xlrd
import csv

import codecs
import json

reload(sys)  
sys.setdefaultencoding('utf8')

def randomword(length):
   return ''.join(random.choice(string.lowercase + string.uppercase + string.digits) for i in range(length))

# Create your views here.

def index(request):
    #for Google drive auth
    client_id = CLIENT_ID
    api_key = API_KEY
    scopes = SCOPES
    return render_to_response('index.html', locals())


def pdf(request, filename, filefolder=None):
    pdf_name = filename
    return render_to_response('redirect.html', locals())


def epub(request, filename):
    return render_to_response('epub.html', locals())

def csvAsTable(request, filename):
    file_path = "%s/%s" % (settings.BASE_DIR + settings.STATIC_URL + 'drop-pdf', filename)

    with open(file_path, 'rU') as file_:
        reader = csv.reader(file_)
        title = reader.next()
        content = [i for i in reader]

    return render_to_response('table.html', locals())


@csrf_exempt
def upload(request):
    filename = ""
    if request.method == 'POST':
        file = request.FILES['file']
        filename = file._get_name()
        
        temp = filename.split('.')
        extension = temp[len(temp) - 1]

        filename = save_file(request.FILES['file'], 'drop-pdf', extension)
            
    return HttpResponse(filename)


def drop(request):
    if 'filename' in request.GET:
        file_path = "%s/%s" % (settings.BASE_DIR + settings.STATIC_URL + 'drop-pdf', request.GET['filename'])
        os.remove(file_path)

    return HttpResponse("")

# save uploaded pdf file and determine whether pdf has text or not.
#   return true-0-<filename> if pdf has text.
#   return false-<pagenum>-<filename>   if pdf has no text and must be ocred.
def save_file(file, path='', extension='pdf'):
    temp = settings.BASE_DIR + settings.STATIC_URL + str(path)

    if not os.path.exists(temp):
        os.makedirs(temp)

    filename = file._get_name()

    #handle non ascii chars in file name
    if isinstance(filename, unicode):
        try:
            filename = unidecode(filename)
        except:
            filename = re.sub(r'[^\x00-\x7F]+','.', filename)


    filename = filename.replace("'", '').replace('"', '')
    filename = re.sub(r"[\(,\),\s]+", "-", filename)


    filename_noextension = '.'.join(filename.split('.')[:-1])
    rand_key = randomword(5)

    filename = filename_noextension + "-" + rand_key + '.' + extension
    
    fd = open('%s/%s' % (temp, str(filename)), 'wb')
    for chunk in file.chunks():
        fd.write(chunk)
    fd.close()

    if extension == "pdf":
        # get total number of pages 
        page_num = count_pages('%s/%s' % (temp, str(filename)))
    
        # check if pdf has text.
        os.system("pdftotext " + temp + "/" + str(filename))
        file_text = filename_noextension + "-" + rand_key + '.txt'
    
        txt_path = temp + "/" + file_text

        if not os.path.exists(txt_path):
            print 'no text'
            return 'none-' + str(page_num) + "-" + filename
        with open(temp + "/" + file_text, 'rb') as f:
            str_data = f.read()
        os.remove(temp + "/" + file_text)

        if len(str_data) < page_num + 10:
            return 'false-' + str(page_num) + "-" + filename
        return 'true-0-' + filename
    elif extension == 'docx' or extension == 'doc':
        # convert docx to pdf
        pdf_name = filename_noextension + "-" + rand_key + '.pdf'
        pdf_path = '%s/%s' % (temp, str(pdf_name))
        docx_to_pdf('%s/%s' % (temp, str(filename)), pdf_path)

        return 'true-0-' + pdf_name
    elif extension == 'xlsx' or extension == 'xls':
        csv_name = filename_noextension + "-" + rand_key + '.csv'
        csv_path = '%s/%s' % (temp, str(csv_name))

        csv_from_excel('%s/%s' % (temp, str(filename)), csv_path)

        return csv_name
    elif extension == 'csv':
        return filename_noextension + "-" + rand_key + '.csv'

    elif extension == 'epub':
        return filename_noextension + "-" + rand_key + '.epub'


        #if epub extraction fails user will be alerted
        if not unzip_epub(temp, filename, filename_noextension, rand_key):
            return False

        filename_w_key = '%s-%s' % (filename_noextension, rand_key)
        full_path = os.path.join(settings.BASE_DIR, 'static', path, filename_w_key) 
        #full_path = 'upload/static/%s/%s' % (path, filename_w_key)
        template_data = process_epub_html(full_path, filename_w_key)
        #if file structure not as expected user will be alerted
        if not template_data:
            return False
        pages = template_data[0]
        styles = template_data[1]
        epub_data = {'pages': pages, 'styles': styles, 'filename': filename_w_key}

        #write a configuration file to be read when file url is requested
        #this data will be used to construct the template
        config_path = full_path + '/toc.json'
        with codecs.open(config_path, 'w', 'utf8') as f:
                 f.write(json.dumps(epub_data, sort_keys = True, ensure_ascii=False))

        return filename_w_key


def ocr(request):
    temp = settings.BASE_DIR + settings.STATIC_URL + "drop-pdf"
    filename = request.GET["filename"]
    
    start = int(round(time.time() * 1000))
    os.system("pypdfocr " + temp + "/" + str(filename))
    end = int(round(time.time() * 1000))
    print "%.2gs" % (end-start)

    new_filename = filename.split(".pdf")[0] + "_ocr" + ".pdf"

    return HttpResponse(new_filename)


@ensure_csrf_cookie
def ocr_pdf(request):
    return render_to_response('ocr_pdf.html')


@csrf_exempt
def ocr_upload_and_check(request):
    pdf_file = request.FILES.get('pdf-file')

    processing_error = None

    filename = pdf_file.name

    if isinstance(filename, unicode):
        try:
            filename = unidecode(filename)
        except:
            filename = re.sub(r'[^\x00-\x7F]+','.', filename)

    filename = filename.replace("'", '').replace('"', '')
    filename = re.sub(r"[\(,\),\s]+", "-", filename)

    extension = filename.split('.')[-1]

    if extension != 'pdf':
        processing_error = 'Not a pdf'

    filename_noextension = '.'.join(filename.split('.')[:-1])

    rand_key = randomword(5)

    filename = filename_noextension + "-" + rand_key + '.' + extension

    save_path = os.path.join(settings.BASE_DIR + settings.STATIC_URL,
            'drop-pdf', filename)

    ocr_file_name = filename_noextension + '-' + rand_key + '_ocr.pdf'

    #save file
    if processing_error is None:
        fd = open(save_path, 'wb')
        for chunk in pdf_file.chunks():
            fd.write(chunk)
        fd.close()

    #see if pdf has text already
    cmd = 'pdftotext "%s" -' % save_path

    txt = subprocess.check_output(cmd, shell=True)

    txt = re.sub('\W', '', txt)

    if len(txt) > 0:
        processing_error = 'This PDF already has text. Use the "Force OCR" button to overwrite text with a fresh OCR if desired.'

    data = {'file_info': {'filename': pdf_file.name, 'size': pdf_file.size,
        'ocr_file_name': ocr_file_name, 'processing_error': processing_error,
        'save_path': save_path, 'ocr_file_name': ocr_file_name}}

    return JsonResponse(data)


@csrf_exempt
def ocr_pdf_result(request):
    force_flag = request.POST.get('force_flag')

    file_info = request.POST.get('file_info')

    file_info = json.loads(file_info)

    save_path = file_info.get('save_path')

    processing_error = 'None'

    if save_path is None:
        processing_error = 'Uploaded file not located.'

    #TODO this can be discarded when system is upgraded and there is a native ocrmypdf command
    # also when there aren't two settings.py files and BASE_DIR is consistant in deploy 
    if 'ocr_pdf' in os.listdir(settings.BASE_DIR):
        cmd_path = os.path.join(settings.BASE_DIR, 'ocr_pdf', 'ocr.sh')

    elif 'ocr_pdf' in os.listdir(os.path.dirname(settings.BASE_DIR)):
        cmd_path = os.path.join(os.path.dirname(settings.BASE_DIR), 'ocr_pdf', 'ocr.sh')

    else:
        processing_error = 'cannot find parser directory'

    if not processing_error:
	cmd = '%s %s' % (cmd_path, save_path)

        if force_flag:
            cmd += ' %s' % 'true'

	p = subprocess.Popen(cmd, shell=True)

    file_info['processing_error'] = processing_error

    data = {'file_info':  file_info}

    return render_to_response('ocr_pdf_result.html', data)


@csrf_exempt
def ocr_pdf_complete(request):
    #check if output file exists yet
    filename = request.POST.get('filename')

    save_path = os.path.join(settings.BASE_DIR + settings.STATIC_URL,
            'drop-pdf', filename)

    if os.path.exists(save_path):
        return JsonResponse({'document_exists': True})
    else:
        raise Http404('file not located yet')


def youtube_video(request, video_id):
    condensed_transcript = []

    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
    except:
        return render_to_response('youtube_not_found.html', {})

    subseconds = 0
    condensed_entry = None
    start_times = [];

    for entry in transcript:
        start = entry.get('start')
        text = entry.get('text', '')
        duration = entry.get('duration', 0)

        text = text.encode('utf-8', 'ignore')
        text = text.replace('\n', ' ')

        try:
            duration = float(duration)
        except:
            continue

        if condensed_entry is None:
            condensed_entry = {'start': start, 'text': text, 'duration': duration}

        else:
            condensed_entry['duration'] += duration
            condensed_entry['text'] += ' ' + text 

        if condensed_entry.get('duration', 0) >= 23:
            condensed_entry['start_display'] = time.strftime('%H:%M:%S', 
                    time.gmtime(condensed_entry.get('start', 0))) 

            s = condensed_entry.get('start', 0)
            start_times.append(s)

            condensed_transcript.append(condensed_entry)
            subseconds = 0
            condensed_entry = None

        #last entry
        elif entry == transcript[-1]:
            condensed_entry['start_display'] = time.strftime('%H:%M:%S', 
                    time.gmtime(condensed_entry.get('start', 0))) 

            s = condensed_entry.get('start', 0)
            start_times.append(s)

            condensed_transcript.append(condensed_entry)


    source = 'https://www.youtube.com/embed/'
    source += video_id
    source += '?enablejsapi=1'
    #source += '?enablejsapi=1&origin='
    #source += 'https://docdrop.org'
    source += '&widgetid=1'
    source += '&start=0&name=me'

    canonical_url = 'https://www.youtube.com/watch?v='
    canonical_url += video_id 

    noembed_url = 'https://noembed.com/embed?url=' + canonical_url 
    r = requests.get(noembed_url)

    title = ''
    if r.status_code == 200:
        try:
            video_info = r.json()
            if video_info:
                title = video_info.get('title')

        except:
            pass


    return render_to_response('youtube.html', {'transcript': condensed_transcript,
        'video_id': video_id, 'start_times': start_times, 'canonical_url': canonical_url, 
        'iframe_src': source, 'title': title})


def count_pages(filename):
    rxcountpages = re.compile(r"/Type\s*/Page([^s]|$)", re.MULTILINE|re.DOTALL)
    data = file(filename,"rb").read()
    return len(rxcountpages.findall(data))


def docx_to_pdf(infilename, outfilename):
    # Extract the text from the DOCX file object infile and write it to 
    # a PDF file.

    #os.system("unoconv --listener")
    os.system("doc2pdf " + infilename)
    '''try:
        infil = opendocx(infilename)
    except Exception, e:
        print "Error opening infilename"
        print "Exception: " + repr(e) + "\n"
        sys.exit(1)

    paragraphs = getdocumenttext(infil)

    pw = PDFWriter(outfilename)
    pw.setFont("Courier", 12)
    #pw.setHeader("DOCXtoPDF - convert text in DOCX file to PDF")
    #pw.setFooter("Generated by xtopdf and python-docx")
    wrapper = TextWrapper(width=70, drop_whitespace=False)

    # For Unicode handling.
    new_paragraphs = []
    for paragraph in paragraphs:
        new_paragraphs.append(paragraph.encode("utf-8"))

    for paragraph in new_paragraphs:
        lines = wrapper.wrap(paragraph)
        for line in lines:
            pw.writeLine(line)
        pw.writeLine("")

    pw.savePage()
    pw.close()'''


def csv_from_excel(excel_file, csv_name):
    workbook = xlrd.open_workbook(excel_file)

    worksheet_name = workbook.sheet_names()[0]

    #all_worksheets = workbook.sheet_names()
    #for worksheet_name in all_worksheets:
    worksheet = workbook.sheet_by_name(worksheet_name)
    your_csv_file = open(csv_name, 'wb')
    wr = csv.writer(your_csv_file, quoting=csv.QUOTE_ALL)

    for rownum in xrange(worksheet.nrows):
        wr.writerow([unicode(entry).encode("utf-8") for entry in worksheet.row_values(rownum)])
    your_csv_file.close()


#TODO CSRF token not working. need to fix this without breaking site, it may have
#been disabled by someone earlier but is important.
@ensure_csrf_cookie
def fingerprinter(request):
    return render_to_response('refingerprint.html')


@csrf_exempt
def fingerprinter_upload(request):
    processed_files = []

    pdf_file = request.FILES.get('pdf-file')
    copy_count = request.POST.get('copy-count', 1)
    suffix = request.POST.get('file-suffix', '')

    try:
        copy_count = int(copy_count)
    except:
        copy_count = 1

    if pdf_file is not None:
        #make save directory 
        rand_path = randomword(9)
        fingerprint_dir = os.path.join(settings.BASE_DIR, 
                settings.STATIC_ROOT, 'fingerprints', rand_path)

        os.makedirs(fingerprint_dir)

        s = os.path.splitext(pdf_file.name)
        filename = s[0].replace("'", '').replace('"', '')

        #handle non ascii chars in file name
        #(strangly only wsgi seems to choke on those)
        if isinstance(filename, unicode):
            try:
                filename = unidecode(filename)
            except:
                filename = re.sub(r'[^\x00-\x7F]+','.', filename)

        extension = s[1] 

        file_content = pdf_file.read()

        content = PdfReader(io.BytesIO(file_content))

        if content.ID is None:
            file_id = 'No ID'
        else:
            file_id = str(content.ID[0]).replace('<', '').replace('>', '')\
                    .replace('(', '').replace(')', '')

        #bad file_ids can contain strange characters
        #TODO When we upgrade
        try:
            file_id.encode('utf-8').strip()
        except UnicodeDecodeError:
            file_id = 'Unreadable'

        file_info = {'filename': pdf_file.name, 'size': pdf_file.size, 'id': file_id, 'directory_name': rand_path}

        for copy_index in range(copy_count):
            if suffix and suffix != '':
                save_filename = filename + '-' + suffix + '-' + str(copy_index + 1) + extension
            else:
                save_filename = filename + '-' + str(copy_index + 1) + extension

            file_path = os.path.join(fingerprint_dir, save_filename)

            static_link = os.path.join('/pdf', save_filename)
            download_link = os.path.join('/static/drop-pdf', save_filename)

            content = PdfReader(io.BytesIO(file_content))

            #add some random meta data
            content.Info.randomMetaData = binascii.b2a_hex(os.urandom(20)).upper()

            #change id to random id
            md = hashlib.md5(filename)
            md.update(str(time.time()))
            md.update(os.urandom(10))

            new_id = md.hexdigest().upper()

            #keep length 32
            new_id = new_id[0:32] 

            while len(new_id) < 32: 
                new_id += random.choice('0123456789ABCDEF')

            content.ID = [new_id, new_id]

            PdfWriter(file_path, trailer=content).write()

            #copy file into online annotator with unique name
            annotation_name = filename + '-' + suffix + '-' \
                    + str(copy_index + 1) + '-' + rand_path + extension

            annotation_path = os.path.join(settings.BASE_DIR, settings.STATIC_ROOT, 
                    'drop-pdf', annotation_name)

            shutil.copy(file_path, annotation_path)

            #For some reason nested directories do not provide files from static.
            #We need to clean up double "settings" file and sanify the basic setup but
            #For now serve the file from a dedicated URL.

            copy_info = {'filename': save_filename,
                    'download_path': os.path.join(rand_path, save_filename),
                    'docdrop_link': annotation_name, 'id': content.ID[0]}

            processed_files.append(copy_info)

    else:
        raise Http404('file not provided')
            

    data = {'processed_files': processed_files, 'file_info': file_info,
            'archive_name': filename}

    return render_to_response('refingerprint_results.html', data)


def fingerprinter_download(request, directory_name, filename):
    file_location = os.path.join(settings.BASE_DIR, 'static/fingerprints',
            directory_name, filename)

    try:    
        with open(file_location, 'r') as f:
           file_data = f.read()

        response = HttpResponse(file_data, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    except IOError:
        response = HttpResponseNotFound('<h1>File does not exist</h1>')

    return response


def fingerprinter_compressed(request, directory_name):
    directory_path = os.path.join(settings.BASE_DIR, 'static/fingerprints',
            directory_name)

    archive_name = request.GET["archive_name"]

    tmp_name = '/tmp/%s' % directory_name
    tmp_zip = tmp_name + '.zip'

    #create zipfile
    content = shutil.make_archive(tmp_name, 'zip', directory_path)

    try:
        with open(tmp_zip, 'rb') as f:
           file_data = f.read()

        response = HttpResponse(file_data, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="%s.zip"' % archive_name
        os.remove(tmp_zip)

    except IOError:
        response = HttpResponseNotFound('<h1>File does not exist</h1>')

    return response
