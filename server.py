#!/usr/bin/python
import sys,os,BaseHTTPServer

class ServerException(Exception):
    '''For internal error reporting.'''
    pass

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    #how to display a directory
    Listing = '''\
    <html>
    <body>
    <ul>
    %s
    </ul>
    </body>
    </html>
    '''

    # How to display an error.
    Error_Page = """\
    <html>
    <body>
    <h1>Error accessing %(path)s</h1>
    <p>%(msg)s</p>
    </body>
    </html>
    """

    def do_GET(self):
        try:
            full_path = os.getcwd() + self.path
            if not os.path.exists(full_path):
                raise ServerException("'%s' not found" % self.path)
            # it is a file 
            elif os.path.isfile(full_path):
                self.handle_file(full_path)
            
	    elif os.path.isdir(full_path):
                self.list_dir(full_path)
            # the path that program can not handle 
            else:
                raise ServerException("Unknown Object '%s'" % self.path)
        except Exception,msg:
            self.handle_error(msg)
    
    def handle_file(self,full_path):
        try:
            with open(full_path,'r') as input:
                content = input.read()
            self.send_content(content)
        except IOError,msg:
            msg = "'%s' can not be read '%s'" % (self.path,msg)
            self.handle_error(msg)

    def handle_error(self,msg):
        content = self.Error_Page % {
                                     'path' : self.path,
                                     'msg'  : msg
                                    }
        self.send_content(content)
    
    def list_dir(self,full_path):
        try:
            entries = os.listdir(full_path)
            bullets = ['<li>%s</li>' % e for e in entries if not e.startswith('.')]
            print bullets
            page = self.Listing % '\n'.join(bullets)
            self.send_content(page)
        except OSError,msg:
            msg = "'%s' cannot be listed: %s" % (self.path, msg)
            self.handle_error(msg)
        
    def send_content(self,content):
        self.send_response(200)
        self.send_header("Content-type","text/html")
        self.send_header("Content-Length",str(len(content)))
        self.end_headers()
        self.wfile.write(content)

if __name__=='__main__':
    serverAddress = ('',8080)
    server = BaseHTTPServer.HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()
