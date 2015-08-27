#!/usr/bin/env python
# -*- coding: utf-8 -*-

#---
#--- Python
import sys
import StringIO
import argparse

#---
#--- 3rd party
from redmine import Redmine
from redmine import exceptions as redmine_exceptions

#---
class ProjectTree(object) :
    def __init__(self, allProjects ) :
        self._projects = list(allProjects)
        self._projectsByName = {} # name -> project
        for project in self._projects :
            self._projectsByName[project.name.encode('utf-8')] = project
        self._projects.sort(key = lambda p : self.getBreadcrumbTrail(p))

    def iter_dfs(self) :
        for project in self._projects :
            yield project

    def getParent(self, project) :
        """
        @return: None or project.parent
        """
        try :
            parentProjectName = project.parent.name.encode('utf-8')
        except AttributeError :
            parentProjectName = ''

        if not parentProjectName :
            parentProject = None
        else :
            parentProject =  self._projectsByName.get(parentProjectName, None)
            if 0 :
                print "DEBUG: parentName = %r" % (parentProjectName,)
                print "DEBUG: parentObject %r" % (parentProject,)
        return parentProject

    def getBreadcrumbTrail(self, project, encoding = 'utf-8') :
        """
        @return: (..., parentName, projectName)
        """
        return list(p.name.encode(encoding) for p in self.getAncestorsAndProject(project))

    def getAncestorProjects(self, project) :

        def _iterAncestors(project) :
            parent = self.getParent(project)
            if parent is None :
                return
            yield parent
            for a in _iterAncestors(parent) :
                yield a

        return list(reversed(list(_iterAncestors(project))))

    def getAncestorsAndProject(self, project) :
        return self.getAncestorProjects(project) + [project]


#---
class PageTree(object) :
    def __init__(self, project, allPages) :
        self._project = project
        self._pages = list(allPages)
        self._pagesByTitle = {} # title -> page
        for page in self._pages :
            self._pagesByTitle[page.title.encode('utf-8')] = page


        self._pagesWithParent = {} # title -> {page -> [childPages, ...]}
        for page in self._pages :
            if 0 :
                print "DEBUG: %r %r" % (project, page,)
            self._insert(page)

        self._pages.sort(key = lambda p : self.getBreadcrumbTrail(p))

    def getParent(self, page) :
        """
        @return: None or page.parent
        """
        try :
            parentPageTitle = page.parent.title.encode('utf-8')
        except AttributeError :
            parentPageTitle = ''

        if not parentPageTitle :
            parentPage = None
        else :
            parentPage =  self._pagesByTitle.get(parentPageTitle, None)
            if 0 :
                print "DEBUG: parentPageTitle = %r" % (parentPageTitle,)
                print "DEBUG: parentPage %r" % (parentPage,)
        return parentPage


    def getBreadcrumbTrail(self, page, encoding = 'utf-8') :
        """
        @return: (..., parentPage, page)
        """
        return list(p.title.encode(encoding) for p in self.getAncestorsAndPage(page))


    def getAncestorPages(self, page) :

        def _iterAncestors(page) :
            parent = self.getParent(page)
            if parent is None :
                return
            yield parent
            for a in _iterAncestors(parent) :
                yield a

        return list(reversed(list(_iterAncestors(page))))

    def getAncestorsAndPage(self, page) :
        return self.getAncestorPages(page) + [page]

    def _insert(self, page) :
        #self._pages.append(page)
        #if parentPage is None :
        #    self.pagesWithParent[page] = []
        return

    def iter_dfs(self) :
        for page in self._pages :
            yield page

#---
def printGlobalIndex(redmineHandle) :
    lineCount = 0
    for line in iterGlobaleIndexLines(redmineHandle) :
        lineCount += 1
        print line
    return lineCount

def iterGlobaleIndexLines(redmineHandle, **keywords) :
    """
    Iterates over the lines of the target document line by line.

    @keyword printProgress: If True progress information will be printed to stdout
    @type    printProgress: bool
    """
    printProgress = keywords.get('printProgress', False)
    baseURL = redmineHandle.url
    r = redmineHandle

    allProjects = r.project.all()
    projectCount = len(allProjects)
    if projectCount == 0 :
        return

    projectTree = ProjectTree(allProjects)

    FIRST_TIME = True

    for (projNum, project) in enumerate(projectTree.iter_dfs()) :
        breadcrumbTrail = " » ".join(projectTree.getBreadcrumbTrail(project))
        pid = project.id # numeric
        projectIdent = project.identifier.encode('utf-8', 'ignore') # symbolic
        pname = project.name

        # singlePage = r.wiki_page.get('Mitarbeiter', project_id = PID)
        # yield singlePage.text

        allPagesQuery =  r.wiki_page.filter(project_id = pid)
        try :
            allPages = list(allPagesQuery)
        except redmine_exceptions.ForbiddenError :
            #print "Cannot access pages of project '%(pident)s'!" % locals()
            allPages = []
        if len(allPages) > 0 :
            if printProgress :
                print "%i/%i:" %(projNum+1, projectCount),
            if FIRST_TIME :
                yield "{{>toc}}"
                yield ""
                yield "h1. Global Index"
                yield ""
                FIRST_TIME = False

            yield ""
            yield "h2. %(breadcrumbTrail)s" % locals()
            yield ""

            pageTree = PageTree(project, allPages)
            for (pageNum,page) in enumerate(pageTree.iter_dfs()) :
                if printProgress :
                    print ".",

                pageTitle = page.title.encode('utf-8', 'ignore')
                prettyPageTitle = pageTitle.replace('_', ' ')
                pageAuthor = page.author.name.encode('utf-8', 'ignore')
                pageCreatedOn = page.created_on
                pageUpdatedOn = page.updated_on
                ancestors = pageTree.getAncestorsAndPage(page) # getAncestorPages(page)
                indentCount = len(ancestors) + 1
                indent = "*" * indentCount
                yield "%(indent)s [[%(projectIdent)s:%(prettyPageTitle)s]]" % locals()
                # yield "%(indent)s %(pageTitle)s (von %(pageAuthor)s) -> %(ancestors)r" % locals()

            if printProgress :
                print ""

            yield ""
            yield '"Hauptseite":%(baseURL)s/projects/%(projectIdent)s/wiki' % locals()
            yield '"Seiten nach Titel sortiert":%(baseURL)s/projects/%(projectIdent)s/wiki/index' % locals()
            yield '"Seiten nach Datum sortiert":%(baseURL)s/projects/%(projectIdent)s/wiki/date_index' % locals()

#---
class CLI(object) :
    """
    Encapsulates the Command Line Interface.
    """
    def __init__(self) :
        self._parser = parser = self._createParser()
        self._args = args = parser.parse_args()
        if args.apikey is None :
            print "You must provide a Redmine API-Key as first argument."
            sys.exit(1)
            return

    def _createParser(self) :
        parser = argparse.ArgumentParser()
        parser.add_argument("--apikey", help = "Valid API-key to use the Python REST-API")
        parser.add_argument("-t", "--targetpage",
                            help = "Fully qualified Name of a Wiki page the result should be stored on",
                            default = "")
        parser.add_argument("-p", "--projectid",
                            help = "Id of the project the target wiki page belongs to",
                            default = "")

        return parser


    def getBaseURL(self) :
        """
        Base URL of the Redmine instance.
        """
        baseURL = 'https://redmine.itz.uni-halle.de'
        return baseURL

    def getApiKey(self) :
        """
        Valid API-key to use the REST-API of Redmine.
        """
        return self._args.apikey

    def getTargetPage(self) :
        """
        @rtype: None or str
        """
        return self._args.targetpage

    def getProjectId(self) :
        return self._args.projectid

#---
def main() :
    cli = CLI()
    baseURL = cli.getBaseURL()
    apiKey = cli.getApiKey()

    redmineHandle = Redmine(baseURL, key = apiKey)


    allProjects = redmineHandle.project.all()
    projectCount = len(allProjects)
    if projectCount == 0 :
        print "You must provide a VALID Redmine API-Key!"
        return

    targetPage = cli.getTargetPage()
    projectId = cli.getProjectId()
    print projectId, targetPage
    if not targetPage or not projectId:
        lineCount = printGlobalIndex(redmineHandle)
    else :
        pageLines = list(iterGlobaleIndexLines(redmineHandle, printProgress = True))
        newText = "\n".join(pageLines)
        oldPage = redmineHandle.wiki_page.get(targetPage, project_id=projectId)
        oldText = oldPage.text.encode('utf-8')
        if oldText != newText :
            redmineHandle.wiki_page.update(targetPage,
                                           project_id = projectId,
                                           title = 'Global index',
                                           text = newText,
                                           parent_title ='',
                                           comments = 'automatisch aktualisiert')

    return

if __name__ == '__main__' :
    #sys_stderr = sys.stderr
    #errbuf = StringIO.StringIO()
    #sys.stderr = errbuf
    try :
        main()
    except KeyboardInterrupt :
        sys.exit(0)
    #sys.stderr = sys_stderr
