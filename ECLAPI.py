import base64
import sys
import os.path
import urllib2, urllib
from urllib2 import HTTPError
try:
    import hashlib
except ImportError:
    try:
        import md5 as hashlib
    except ImportError:
        print("Failed to import hashlib or md5")
        sys.exit(1)

import random

try:
    # Python 2.5+
    import xml.etree.ElementTree as etree
#   print("running with ElementTree on Python 2.5+")
except ImportError:
    try:
        # normal ElementTree install
        import elementtree.ElementTree as etree
#       print("running with ElementTree")
    except ImportError:
        print("Failed to import ElementTree from any known place")
        sys.exit(1)

class ECLAPIException(Exception):
    def __init__(self, value):
        self.value = value
        
    def __str__(self):
        return repr(self.value)

class ECLHTTPError(ECLAPIException):
    def __init__(self, code, msg, body):
        self.Code = code
        self.Message = msg
        self.Body = body
        
    def __str__(self):
        return '%s %s' % (self.Code, self.Body)

class ECLConnection:

    SignatureMethod = "md5"

    def __init__(self, url, username=None, password=None, xml_user=True):
        '''
        '''
        self._url = url
        self._username = username
        self._password = password
        

    def _make_salt(self):
        m = hashlib.new('md5')
        m.update("%s" % (random.randint(1,1234567890),))
        return m.hexdigest()


    def _signature(self, method, args, body):
        text = '%s:%s:%s' % (args, self._password, body)
        h = None
        if method == 'sha1':
            h = hashlib.sha1()
        elif method == 'md5':
            h = hashlib.md5()
        elif method == 'sha512':
            h = hashlib.sha512()
        if h == None:
            return None
        h.update(text)
        return h.hexdigest() 


    def _add_signature(self, req, args, body):
        if self._username:
            req.add_header("X-Signature-Method", self.SignatureMethod)
            req.add_header("X-User", self._username)
            #req.add_header("HTTP_X_USER_NAME", self._username)
            req.add_header("X-Signature", 
                self._signature(self.SignatureMethod, args, body))

    def post(self, entry):
        '''
        '''
        if self._username:
            entry.setAuthor(self._username)
        params = entry.xshow().strip()
        args = "salt=%s" % (self._make_salt(),)
        req = urllib2.Request(url=self._url + '/E/xml_post' +
            '?' + args, data=params)
        #print 'Signature: '+ self.calculate_signature(self._password + ":" + params, 
                    #self.SignatureMethod)
        req.add_header("Content-type", "text/xml")
        if self._url.startswith("https:"):
            #req.add_header("X-User", self._username)
            req.add_header("X-Password", self._password)
        self._add_signature(req, args, params)
        try:
            response = urllib2.urlopen(req)
        except HTTPError, err:
            return err.code, err.msg, err.fp.read()
            
        data = response.read()

        #print data  # DEBUG
        return response.code, response.msg, data

    def close(self):
        pass

    def list(self, category=None, form=None, tag=None,
            limit=None, after=None):
        args = ['o=ids', 'salt=%s' % (self._make_salt(),)]
        if category:
            args.append('c=%s' % (urllib.quote_plus(category,)))
        if form:
            args.append('f=%s' % (urllib.quote_plus(form,)))
        if after:
            if type(after) != type(''):
                after = after.strptime('%Y-%m-%d %H:%M:%S')
            args.append('a=%s' % (urllib.quote_plus(after),))
        if tag:
            args.append('t=%s' % (tag,))
        if limit:
            args.append('l=%s' % (limit,))

        url = self._url + '/E/xml_search'
        args = '&'.join(args)
        
        if args:
            url += '?' + args
        req =  urllib2.Request(url=url)
        self._add_signature(req, args, '')
        #print 'Signature: '+ self.calculate_signature(self._password + ":" + params, 
        #            self.SignatureMethod)
        
        try:
            response = urllib2.urlopen(req)
        except HTTPError, error:
            raise ECLHTTPError(error.code, error.msg, error.fp.read()) 
        tree = etree.parse(response)
        entries = tree.findall('entry')
        return [int(e.attrib.get('id')) for e in entries]
        
    def get(self, eid):
        args = ['e=%s' % (eid,), 'salt=%s' % (self._make_salt(),)]
        url = self._url + '/E/xml_get'
        args = '&'.join(args)
        if args:
            url += '?' + args
        req =  urllib2.Request(url=url)
        self._add_signature(req, args, '')
        response = urllib2.urlopen(req)
        return response.read()        
        
        
        
class ECLEntry:

    def __init__(self, category, tags=[], formname='default', text='', preformatted=False,
                private=False):
        self._category = category
        self._tags = tags
        self._formname = formname
        self._text = text
        # Create the top level element
        self._entry = etree.Element('entry', category=category)
        if not preformatted:
            self._entry.attrib['formatted']='formatted'
        if private:
            self._entry.attrib['private'] = 'yes'
        # Create the form
        self._form = etree.SubElement(self._entry, 'form', name=formname)
        if text:
            # Create the text field
            textfield = etree.SubElement(self._form, 'field', name='text')
            # Store the text
            textfield.text = text
        for tag in tags:
            etree.SubElement(self._entry, 'tag', name=tag)

    def setValue(self, name, value):
        # Create the field
        field = etree.SubElement(self._form, 'field', name=name)
        # Store the text 
        field.text = value

    def setAuthor(self, name):
        self._entry.attrib['author'] = name

    def addAttachment(self, name, filename, data=None):
        # Create the field
        field = etree.SubElement(self._entry, 'attachment', type='file', name=name, filename=os.path.basename(filename))
        if data:
            # Store the text 
            field.text = base64.b64encode(data)
        else:
            f = open(filename,'r')
            b = f.read()
            field.text = base64.b64encode(b)
            f.close()

    def addImage(self, name, filename, image=None):
        # Create the field
        field = etree.SubElement(self._entry, 'attachment', type='image', name=name, filename=os.path.basename(filename))
        # Store the text 
        if image:
            # Store the text 
            field.text = base64.b64encode(image)
        else:            
            f = open(filename,'r')
            b = f.read()
            field.text = base64.b64encode(b)
            f.close()
                                
    def xshow(self):
        return etree.tostring(self._entry)



