#!/usr/bin/python
# encoding: utf-8

import sys
import functools

from workflow import Workflow, ICON_WARNING

base_url = "http://dblp.uni-trier.de/search?q="
bib_url = "http://dblp.uni-trier.de/rec/bibtex/"

# How long to cache results for - in seconds
CACHE_MAX_AGE = 1

# Minimun score for filtering
FILTER_MIN_SCORE = 10


def getpubs():
    import urllib2
    # import requests
    from pyquery import PyQuery as pq

    term = "afrati"
    results_html = pq(urllib2.urlopen(base_url+term).read())
    entries = results_html(".entry")
    papers = []
    for i in range(len(entries)):
        paper = {}
        paperid = entries.eq(i).attr("id")
        title = entries.eq(i).find(".title").text()
        subtitle = []
        authors = results_html('.entry').eq(i).find("span[itemprop=author]")
        for a in range(len(authors)):
            subtitle.append(authors.eq(a).text())
        subtitle = ", ".join(subtitle) + year_published
        paper[paperid] = (title, subtitle)
        papers.append(paper)
    return papers


def getpubs2(query, authors=None):
    import urllib2
    # import requests
    from pyquery import PyQuery as pq

    term = query
    results_html = pq(urllib2.urlopen(base_url+term).read())
    # print results_html
    entries = results_html(".entry")
    papers = []
    for i in range(len(entries)):
        paper = {}
        paperid = entries.eq(i).attr("id")
        title = entries.eq(i).find(".title").text()
        subtitle = []
        authors = results_html('.entry').eq(i).find("span[itemprop=author]")
        for a in range(len(authors)):
            subtitle.append(authors.eq(a).text())
        subtitle = ", ".join(subtitle)

        venue = entries.eq(i).find("span[itemprop=isPartOf]").text()
        datePublished = results_html('.entry').eq(i).find("span[itemprop=datePublished]").text()

        subtitle = subtitle + "  " + datePublished + " " + venue

        paper[paperid] = (title, subtitle)
        papers.append(paper)
    # print papers
    return papers


def search_key_for_paper(paper):
    """Generate a string search key for a paper
    """
    for paperid, (title, subtitle) in paper.iteritems():
        elements = []
        elements.append(title)  # title of post
        elements.append(subtitle)  # authors
        # elements.append(paper['extended'])  # description
    return u' '.join(elements)


def main(wf):

    # Get query from Alfred
    if len(wf.args):
        query = wf.args[0]
    else:
        query = None

    # Empty query, prompt for terms
    if not query:
            wf.add_item("Search DBLP",
                        "",
                        arg=0,
                        valid=True,)
            wf.send_feedback()
            return 0

    words = query.split(' ')
    query = []
    # filters = []
    author_filters = []
    year = ""

    for word in words:
        if word.startswith('a:'):  # + words are filters
            if word != 'a:':  # Ignore empty tags
                author_filters.append(word[2:])
        elif word.startswith('.'):  # . for authors
                author_filters.append(word[1:])
        elif word.startswith("year:"):
                year = word[5:]
        else:
            query.append(word)

    query = '+'.join(query)
    if author_filters:
        author_filters = '{1}{0}{2}'.format(": author:".join(author_filters),
                                            'author:',
                                            ':')
        query = query + '+' + author_filters
    if year:
        query = query + '+' + ':year:%s:' % year
    # print query

    # Retrieve posts from cache if available and no more than 600
    # seconds old
    # papers = wf.cached_data('papers', getpubs, max_age=60)
    papers = wf.cached_data('papers',
                            functools.partial(getpubs2, query, None),
                            max_age=CACHE_MAX_AGE)
    # If script was passed a query, use it to filter posts
    # if filters:
    #     papers = wf.filter(filters,
    #                        papers,
    #                        key=search_key_for_paper,
    #                        min_score=FILTER_MIN_SCORE)
    if not papers:
        wf.add_item('No papers found',
                    'Try a different query',
                    icon=ICON_WARNING)

    for paper in papers:
        for paperid, (title, subtitle) in paper.iteritems():
            wf.add_item(title,
                        subtitle,
                        arg=bib_url+paperid,
                        valid=True,)

    # Send output to Alfred. You can only call this once.
    # Well, you *can* call it multiple times, but Alfred won't be listening
    # any more...
    wf.send_feedback()


if __name__ == '__main__':
    # Create a global `Workflow` object
    wf = Workflow(libraries=['./lib'])
    # Call your entry function via `Workflow.run()` to enable its helper
    # functions, like exception catching, ARGV normalization, magic
    # arguments etc.
    sys.exit(wf.run(main))
