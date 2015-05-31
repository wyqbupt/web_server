#!/usr/bin/python
import sys,os,BaseHTTPServer,mimetypes

class ServerException(Exception):
    '''For internal error reporting.'''
    pass

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):

    #root directory we can acess
    Root_Directory = None
    #Debug mode defaultly set down
    Debug = False
    #ERROR code
    ERR_NO_PERMIT = 403
    ERR_NO_FOUND = 404
    ERR_INTERNAL = 500

    #MIME types of files,a dictionary
    File_Types = mimetypes.types_map

    #filename extensions that identify executables.
    Exec_Extensions = {
        ".py" : None
    }
    def do_GET(self):
        #Create log 
        self.log("path is '%s'" % self.path)
        try:
            if self.Root_Directory is None:
                self.err_internal("Root_Directory not Set")
                return 

            abs_path,query_params = self.parse_path()
            self.log("query_params is '%s'" % query_params)
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
                if self.is_executable(abs_path):
                    self.log("abs_path is an executable")
                    self.handle_executable(abs_path,query_params)
                else:
                    self.log("abs_path is a file")
                    self.handle_static_file(abs_path)

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

    def parse_path(self):
        parts = self.path.split("?")
        #no query string
        if len(parts) == 1:
            request_path,queryString = self.path,""
        #have query string
        elif len(parts) == 2:
            request_path,queryString = parts
        else:
            pass

        head = os.path.abspath(self.Root_Directory)
        result = os.path.normpath(head+request_path)
        return result,queryString

    def is_parent_dir(self,left,right):
        return os.path.commonprefix([left,right]) == left

    def guess_file_type(self,path):
        #ext can fetch Extension name
        base,ext = os.path.splitext(path)
        if ext in self.File_Types:
            return self.File_Types[ext]
        #make ext to lower case to do search again
        ext = ext.lower()
        if ext in self.File_Types:
            return self.File_Types[ext]
        return self.File_Types['']

    def is_executable(self,abs_path):
        root,ext = os.path.splitext(abs_path)
        return ext in self.Exec_Extensions

    def handle_executable(self,abs_path,params):
        if params:
            os.environ["REQUEST_METHOD"] = "GET"
            os.environ["QUERY_STRING"] = params
        cmd = "python " + abs_path
        childInput,childOutput = os.popen2(cmd)
        childInput.close()
        response = childOutput.read()
        childOutput.close()
        self.log("handle_executable: response length is %d" % len(response))
        self.send_response(200)
        self.wfile.write(response)

    def handle_static_file(self,abs_path):
        try:
            input = open(abs_path,"rb")
            content = input.read()
            input.close()
            fileType = self.guess_file_type(abs_path)
            self.send_content(content,fileType)
        except IOError,msg:
            msg = "'%s' can not be read '%s'" % (self.path,msg)
            self.err_no_perm(msg)

    def handle_dir(self,abs_path):
        # How to display a single item in a directory listing.
        listing_item = "<li>%s</li>"

        # How to display a whole page of listings.
        listing_page = \
            "<html>" + \
            "<body>" + \
            "<h1>Listing for " + "%(path)s" + "</h1>" + \
            "<ul>" + \
            "%(filler)s" + \
            "</ul>" + \
            "</body>" + \
            "</html>"

        try:
            listing = os.listdir(abs_path)
            filler = '\n'.join([(Listing_Item % item) for item in listing])

            content = listing_page % {
                                            'path'  : self.path,
                                            'filler': filler
                                          }
            self.send_content(content)

        except IOError,msg:
            msg = "'%s' cannot be listed: %s" % (self.path, msg)
            self.send_error(self.ERR_NO_PERMIT,msg)

    def send_content(self,content,fileType="text/html"):
        length = str(len(content))
        self.log("sending content, fileType '%s', length %s" % (fileType, length))
        self.send_response(200)
        self.send_header("Content-type",fileType)
        self.send_header("Content-Length",length)
        self.end_headers()
        self.wfile.write(content)

    def err_internal(self,msg):
        self.send_error(self.ERR_INTERNAL,msg)

    def err_not_found(self,abs_path):
        self.send_error(self.ERR_NO_FOUND,"'%s' not found" % self.path)

    def err_no_perm(self,msg):
        self.send_error(self.ERR_NO_PERMIT,msg)

    #Handle execution errors
    def err_exec(self,msg):
        self.send_error(self.ERR_NO_PERMIT,msg)

    def log(self,msg):
        if self.Debug:
            print msg

#---------------------------------------------------------------------------

if __name__=='__main__':

    import getopt

    #how to handle fatal startup errors
    def fatal(msg):
        print >> sys.stderr, "fatal error:", msg
        sys.exit(1)

    #Defaults
    host = ''
    port = 8080
    root = None

    #Usage notification
    Usage = "server.py [-h host] [-p port] [-v] -r|root_directory"

    options,rest = getopt.getopt(sys.argv[1:],"h:p:rv")

    for (flag,arg) in options:
        if flag == "-v":
            RequestHandler.Debug = True
        elif flag == "-h":
            host = arg
            if not arg:
                msg = "No host given with -h"
                fatal(msg)
        elif flag == "-p":
            try:
                port = int(arg)
            except ValueError, msg:
                fatal("Unable to convert '%s' to integer: %s" % (arg, msg))
        elif flag == "-r":
            root = os.getcwd()
        else:
            fatal(Usage)
    # Make sure root directory is set, and is a directory.
    if (root and rest) or (not root and not rest):
        fatal(Usage)
    if not root:
        root = os.path.abspath(rest[0])
    if not os.path.isdir(root):
        fatal("No such directory '%s'" % root)

    RequestHandler.Root_Directory = root

    serverAddress = ('',8080)
    server = BaseHTTPServer.HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()
