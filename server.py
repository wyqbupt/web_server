#!/usr/bin/python
import sys,os,BaseHTTPServer

class ServerException(Exception):
    '''For internal error reporting.'''
    pass

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    Root_Directory = None
    Debug = False
    ERR_NO_PERMIT = 403
    ERR_NO_FOUND = 404
    ERR_INTERNAL = 500
    # How to display a single item in a directory listing.
    Listing_Item = "<li>%s</li>"
   
    # How to display a whole page of listings.
    Listing_Page = """\
    <html>
    <body>
    <h1>Listing for %(path)s</h1>
    <ul>
    %(filler)s
    </ul>
    </body>
    </html>
    """

    def do_GET(self):
        #Create log 
	self.log("path is '%s'" % self.path)
        try:
	    if self.Root_Directory is None:
		self.err_internal("Root_Directory not Set")
		return 
	    abs_path = self.create_abs_path()
	    self.log("abs_path is '%s'" % abs_path)
	    if not self.is_parent_dir(self.Root_Directory,abs_path):
		self.log("abs_path not below root directory")
		msg = "Path '%s' not below root directory '%s'" % \
		       (abs_path,self.Root_Directory)
		self.err_no_perm(msg)
           
	    #is does not exist
	    elif not os.path.exists(abs_path):
		self.log("abs_path '%s'does not exist" % abs_path)
		self.err_not_found(abs_path)

	    # it is a file 
            elif os.path.isfile(abs_path):
		self.log("abs_path is a file")
                self.handle_file(abs_path)
           
	    #it is a directory
	    elif os.path.isdir(abs_path):
		self.log("abs_path is a directory")
                self.handle_dir(abs_path)
           
	    #the path that program can not handle 
            else:
	        self.log("can not tell what abs_path is")
		self.err_not_found(abs_path)

        except Exception,msg:
            self.err_internal("Unexpected exception: %s" % msg)
  
    def create_abs_path(self):
	head = os.path.abspath(self.Root_Directory)
	result = os.path.normpath(head+self.path)
	return result
   
    def is_parent_dir(self,left,right):
	return os.path.commonprefix([left,right]) == left

    def handle_file(self,abs_path):
        try:
            input = open(abs_path,'r')
            content = input.read()
	    input.close()
            self.send_content(content)
        except IOError,msg:
            msg = "'%s' can not be read '%s'" % (self.path,msg)
            self.err_no_perm(msg)
    
    def handle_dir(self,abs_path):
        try:
            listing = os.listdir(abs_path)
            filler = '\n'.join([(self.Listing_Item % item) for item in listing])

	    content = self.Listing_Page % {
					    'path'  : self.path,
					    'filler': filler
					  }
            self.send_content(content)
        except OSError,msg:
            msg = "'%s' cannot be listed: %s" % (self.path, msg)
            self.send_error(self.ERR_NO_PERMIT,msg)
    
    def send_content(self,content):
        self.send_response(200)
        self.send_header("Content-type","text/html")
        self.send_header("Content-Length",str(len(content)))
        self.end_headers()
        self.wfile.write(content)
    
    def err_internal(self,msg):
	self.send_error(self.ERR_INTERNAL,msg)
    
    def err_not_found(self,abs_path):
	self.send_error(self.ERR_NO_FOUND,"'%s' not found" % self.path)

    def err_no_perm(self,msg):
	self.send_error(self.ERR_NO_PERMIT,msg)

    def log(self,msg):
	if self.Debug:
	    print msg
    

if __name__=='__main__':
    
    import getopt

    Usage = "server.py [-v] root_directory"

    options,rest = getopt.getopt(sys.argv[1:],"v")

    for (flag,arg) in options:
	if flag == '-v':
	    RequestHandler.Debug = True
	else:
	    print >> sys.stderr,"Input Error,the Usage shows below\n"+Usage
	    sys.exit(1)
	
    if not rest:
	print >> sys.stderr,"Input Error,the Usage shows below\n"+Usage
	sys.exit(1)
    root = os.path.abspath(rest[0])
    if not os.path.isdir(root):
	print >> sys.stderr,"No such directory '%s'" % root
	sys.exit(1)
    RequestHandler.Root_Directory = root
    
    serverAddress = ('',8080)
    server = BaseHTTPServer.HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()
