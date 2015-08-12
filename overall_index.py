#!/usr/bin/env python
# -*- coding: utf-8 -*-

#---
#--- Python
import sys
import StringIO

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
def printGlobalIndex(baseURL, apiKey) :
    r = Redmine(baseURL, key = apiKey)

    allProjects = r.project.all()
    projectCount = len(allProjects)
    if projectCount == 0 :
        return 0

    projectTree = ProjectTree(allProjects)

    FIRST_TIME = True
    pageCount = 0

    for project in projectTree.iter_dfs() :
        breadcrumbTrail = " >> ".join(projectTree.getBreadcrumbTrail(project))
        pid = project.id # numeric
        projectIdent = project.identifier.encode('utf-8', 'ignore') # symbolic
        pname = project.name

        # singlePage = r.wiki_page.get('Mitarbeiter', project_id = PID)
        # print singlePage.text

        allPagesQuery =  r.wiki_page.filter(project_id = pid)
        try :
            allPages = list(allPagesQuery)
        except redmine_exceptions.ForbiddenError :
            #print "Cannot access pages of project '%(pident)s'!" % locals()
            allPages = []
        if len(allPages) > 0 :

            if FIRST_TIME :
                print "{{>toc}}"
                print ""
                print "h1. Global Index"
                print ""
                FIRST_TIME = False

            print ""
            print "h2. %(breadcrumbTrail)s" % locals()
            print ""

            pageTree = PageTree(project, allPages)
            for page in pageTree.iter_dfs() :
                pageCount +=1

                pageTitle = page.title.encode('utf-8', 'ignore')
                prettyPageTitle = pageTitle.replace('_', ' ')
                pageAuthor = page.author.name.encode('utf-8', 'ignore')
                pageCreatedOn = page.created_on
                pageUpdatedOn = page.updated_on
                ancestors = pageTree.getAncestorsAndPage(page) # getAncestorPages(page)
                indentCount = len(ancestors) + 1
                indent = "*" * indentCount
                print "%(indent)s [[%(projectIdent)s:%(prettyPageTitle)s]]" % locals()
                # print "%(indent)s %(pageTitle)s (von %(pageAuthor)s) -> %(ancestors)r" % locals()

            print ""
            print '"Hauptseite":%(baseURL)s/projects/%(projectIdent)s/wiki' % locals()
            print '"Seiten nach Titel sortiert":%(baseURL)s/projects/%(projectIdent)s/wiki/index' % locals()
            print '"Seiten nach Datum sortiert":%(baseURL)s/projects/%(projectIdent)s/wiki/date_index' % locals()


#---
def main() :
    baseURL = 'https://redmine.itz.uni-halle.de'
    try :
        apiKey = sys.argv[1]
    except IndexError :
        print "You must provide a Redmine API-Key as first argument."
        sys.exit(1)

    pageCount = printGlobalIndex(baseURL, apiKey)

    if pageCount == 0 :
        print "You must provide a VALID Redmine API-Key!"
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
