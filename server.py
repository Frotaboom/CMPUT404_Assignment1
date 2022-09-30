#  coding: utf-8 
import socketserver
import os

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

class MyWebServer(socketserver.BaseRequestHandler):

    baseUrl = "localhost:8080"

    #sends a 200 OK response. Takes a path to a file to send back to the client
    def response200(self, validatedPath):
        packet = "HTTP/1.1 200 OK\r\n"
        packet += "Server: " + self.baseUrl + "\r\n"
        fileType = validatedPath.split('.')[len(validatedPath.split('.'))-1]
        packet += "Content-Type: text/" + fileType + "\r\n"
        packet += '\r\n'
        packet += self.getFile(validatedPath)
        self.request.sendall(bytearray(packet, 'utf-8'))

    #sends a 301 response with a URI to give to the client for the place the client should go to
    def response301(self, URI):
        packet = "HTTP/1.1 301 Permanently Moved\r\n"
        packet += "Server: " + self.baseUrl + "\r\n"
        packet += "Location: " + URI + "\r\n\r\n"  
        self.request.sendall(bytearray(packet, 'utf-8'))

    #sends a 404 response to the client informing them that their requested path does not exist
    def response404(self):
        packet = "HTTP/1.1 404 Not Found\r\n"
        packet += "Server: " + self.baseUrl + "\r\n\r\n"
        self.request.sendall(bytearray(packet, 'utf-8'))

    #sends a 405 response letting the client know that their method is not being handled
    def response405(self):
        packet = "HTTP/1.1 405 Method Not Allowed\r\n"
        packet += "Server: " + self.baseUrl + "\r\n\r\n"
        self.request.sendall(bytearray(packet, 'utf-8'))

    #takes in a request and sends out 405s for all non-get requests and invalid requests
    #and returns a path for further processing on valid get requests
    def processRequest(self):
        intake = self.data.decode('utf-8')
        lines = intake.split('\r\n')

        if len(lines) == 0:
            #blank request - 405
            return False
    
        firstLine = lines[0].split(' ')
        if len(firstLine) == 0:
            #blank first line - 405
            return False

        typeRequest = firstLine[0]
        if typeRequest.lower() != 'get':
            #unhandled HTTP request - 405
            return False

        return self.percentDecode(firstLine[1])

    #from stack overflow: https://stackoverflow.com/questions/16566069/url-decode-utf-8-in-python
    #replaces all % characters with their ASCII equivalents
    def percentDecode(self, string):
        decodedString = ""
        idx = 0
        while idx < len(string):
            if string[idx] == '%':
                byteArray = bytearray()
                byteArray.append(int(string[idx+1:idx+3], 16))
                decodedString += byteArray.decode('utf-8')
                idx += 3
            else:
                decodedString += string[idx]
                idx += 1

        return decodedString

    #returns False for a path that does not exist
    #returns the path to the FILE request
    #if requested a dir, returns a path to the "index.html" file in that folder (if exists)
    def validateFilePath(self, path):
        if "/./" in path:
            return False

        if path in ("", "/", "/index.html"):
            return "/index.html"

        pathPoints = path.split('/')
        pathLength = len(pathPoints)
        if pathPoints[pathLength-1] == "":
            pathLength -= 1

        pathToReturn = ""
        for pathCounter in range(1, pathLength):
            nextSegment = pathPoints[pathCounter]
            proceed = False
            for root, dirs, files in os.walk("./www" + pathToReturn):
                if pathCounter + 1 >= pathLength:
                    for name in files:
                        if name == nextSegment:
                            return pathToReturn + "/" + nextSegment

                    for name in dirs:
                        if name == nextSegment:
                            #last segment is a dir. Should return the index.html of this dir
                            pathToReturn += "/" + nextSegment
                            finalDirsChildren = os.walk("./www" + pathToReturn)
                            for root2, finalDirs, finalFiles in finalDirsChildren:
                                for fileName in finalFiles:
                                    if fileName == "index.html":
                                        return pathToReturn + "/index.html"
                    return False

                for name in dirs:
                    if nextSegment == name:
                        pathToReturn += "/" + nextSegment
                        proceed = True
                        break

                if proceed:
                    continue
                return False

        return False

    #removes "index.html" from a path if its there
    def convertPathToURI(self, path):
        pathSplits = path.split('/')
        URI = path
        if pathSplits.pop() == "index.html":
            URI = "/".join(pathSplits)
            URI += "/"

        return URI

    #returns the chars of a file given to a path
    #assumes the path is valid
    def getFile(self, path):
        f = open("./www"+path, "r")
        return f.read()
    

    def handle(self):
        self.data = self.request.recv(1024).strip()

        path = self.processRequest()
        if not path:
            self.response405()
            return
        
        validatedPath = self.validateFilePath(path)
        if not validatedPath:
            self.response404()
            return

        URI = self.convertPathToURI(validatedPath)
        if path == URI:
            self.response200(validatedPath)
        else:
            self.response301(URI)

        self.response404()

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()


