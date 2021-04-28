import requests
import argparse
import concurrent.futures
from urllib.parse import urlsplit, parse_qs
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

parser = argparse.ArgumentParser(description="Simple response check script"
                                 )

parser.add_argument('-d', '--document', type=str, metavar='', required=True, help=".txt file with urls")

parser.add_argument('-o', '--output', type=str, metavar='', required=True, help="output path")

parser.add_argument('-q', '--query_focus', required=False, help="get urls that has parameters", action='store_true')

parser.add_argument('-i', '--interesting', required=False, help="get urls that has interesting parameters", action='store_true')

parser.add_argument('-r_ex', '--exc_responses', type=str, metavar='', default="400,404", required=False,
                    help="HTTP codes to exlude in search"
                         "eg: '404,400,'")

parser.add_argument('-t', '--threads', type=int, metavar='', required=False, default=3, help="number of threads, "
                                                                                             "default is 3")
INTERESTING_PARAMETERS = ['id', 'page', 'dir', 'search', 'category', 'file', 'class', 'url', 'news', 'item', 'menu',
                          'lang', 'name', 'ref', 'title', 'view', 'topic', 'thread', 'type', 'date', 'form', 'join',
                          'main', 'nav', 'region', 'cat', 'dir', 'action', 'board', 'date', 'detail', 'file',
                          'download',
                          'path', 'folder', 'prefix', 'include', 'page', 'inc', 'locate', 'show', 'doc', 'site', 'type',
                          'view', 'content', 'document', 'layout', 'mod', 'conf', 'next', 'url', 'target', 'rurl',
                          'dest',
                          'destination', 'redir', 'redirect_uri', 'redirect_url', 'redirect', '/redirect/',
                          '/cgi-bin/redirect.cgi?',
                          '/out/', '/out?', 'view', '/login?to', 'image_url', 'go', 'return', 'returnTo', 'return_to',
                          'checkout_url', 'continue', 'return_path', 'cmd', 'exec', 'command', 'execute', 'ping',
                          'query',
                          'jump', 'code', 'reg', 'do', 'func', 'arg', 'option', 'load', 'process', 'step', 'read',
                          'function',
                          'req', 'feature', 'exe', 'module', 'payload', 'run', 'print', 'dest', 'redirect', 'uri',
                          'path',
                          'continue', 'url', 'window', 'next', 'data', 'reference', 'site', 'html', 'val', 'validate',
                          'domain', 'callback', 'return', 'page', 'feed', 'host', 'port', 'to', 'out', 'view', 'dir',
                          'q', 's', 'search', 'id', 'lang', 'keyword', 'query', 'page', 'keywords', 'year', 'view',
                          'email',
                          'type', 'name', 'p', 'month', 'immagine', 'list_type', 'url', 'terms', 'categoryid', 'key',
                          'l', 'begindate', 'enddate']

INTERESTING_PARAMETERS = list(dict.fromkeys(INTERESTING_PARAMETERS))
remove_these_params = []
INTERESTING_PARAMETERS = list(set(INTERESTING_PARAMETERS)-set(remove_these_params))

args = parser.parse_args()
doc_path = args.document
codes_to_exclude = args.exc_responses.split(',')
thread_num = args.threads
query_focus = args.query_focus


def get_targets(path_):
    targets = []
    with open(path_, 'r') as file:
        for line_ in file:
            targets.append(line_.rstrip('\n'))
    return targets


def get_interesting(end_dict):
    interesting_endpoints = {}
    found_params = {}
    for url_key in end_dict.keys():
        is_interesting = False
        not_added = True
        parameters_dict = end_dict[url_key]
        for i_param in INTERESTING_PARAMETERS:
            for url_param in parameters_dict.keys():
                if i_param in url_param:
                    # print(f"Interesting parameter found: {url_param}")
                    is_interesting = True
                    if i_param in found_params.keys():
                        num_found = found_params[i_param] + 1
                        found_params[i_param] = num_found
                    else:
                        found_params[i_param] = 1
            if is_interesting:
                if not_added:
                    interesting_endpoints[url_key] = end_dict[url_key]
                    not_added = True
                else:
                    pass
    print(f"Found {len(interesting_endpoints.keys())} endpoints with interesting parameters...")
    print(f"Parameters found:   ")
    for key in found_params.keys():
        print(f"Param: {key}: {found_params[key]}")
    return interesting_endpoints

def check_target(target, exclude_codes=codes_to_exclude):
    try:
        print(f"Checking {target}...")
        r = requests.get(target, timeout=8, verify=False)
        # print(f"Checked {target} .... {r.status_code}")
        if str(r.status_code) not in exclude_codes:
            print(f"Found url: {target}   ... {r.status_code}")
            to_write = target
            return to_write
        else:
            return None
    except:
        return None


print("Getting Targets...")
target_urls_all = get_targets(doc_path)
print(f"Found {len(target_urls_all)} targets...")
print("Removing duplicates...")
target_urls = list(dict.fromkeys(target_urls_all))
print(f"Removed {len(target_urls_all) - len(target_urls)} urls, {len(target_urls)} remain after removing duplicates...")
if query_focus:
    print("Removing urls with no known queries")
    new_targets = []
    for t_url in target_urls:
        if urlsplit(t_url).query != '':
            new_targets.append(t_url)
    print(f"Removed {len(target_urls) - len(new_targets)} urls, Remaining: {len(new_targets)}")
    target_urls = new_targets

print("Finding unique endpoints")
# Parse urls, get
endpoint_dict = {}  # {url_str:{p1:x,p2:y,p3:z,p4:f,p5:g}}
all_query_parameters = []
id = 0
new_percentage = 0
for my_url in target_urls:
    id += 1
    old_percentage = new_percentage
    new_percentage = round(((id / len(target_urls)) * 100))
    if old_percentage != new_percentage and new_percentage % 10 == 0:
        print(f"{new_percentage}%")
    url_parsed = urlsplit(my_url)
    url_str = url_parsed.scheme + "://" + url_parsed.netloc + url_parsed.path  # url without query parameters
    query_parsed = parse_qs(url_parsed.query)
    for p in query_parsed.keys():
        all_query_parameters.append(p)

    if url_str not in endpoint_dict.keys():  # This is a unique url path, haven't seen it before in targers
        endpoint_dict[url_str] = query_parsed
    else:
        known_qs = endpoint_dict[url_str]
        if set(known_qs.keys()) == set(query_parsed.keys()):
            # All elements parameters are same in two urls, no need to do anything
            pass
        else:
            # Get the difference, create new dict with all known parameters
            difference = list(set(query_parsed.keys()) - set(
                known_qs.keys()))  # returns a list of parameters that only exists in new url
            tmp_dict = known_qs.copy()
            for key in difference:
                tmp_dict[key] = query_parsed[key]
            endpoint_dict[url_str] = tmp_dict

all_query_parameters = list(dict.fromkeys(all_query_parameters))
print(f"Found {len(endpoint_dict.keys())} unique endpoints and {len(all_query_parameters)} unique parameters...")

print("Checking endpoints...")
if args.interesting:
    print("Checking for endpoints with interesting parameters...")
    target_endpoints = get_interesting(endpoint_dict).copy()
else:
    target_endpoints = endpoint_dict.copy()


with concurrent.futures.ThreadPoolExecutor(max_workers=thread_num) as executor:
    results = executor.map(check_target, target_endpoints.keys())

alive_endpoints = [x for x in results if x is not None]
alive_endpoint_dict = {}

for key in alive_endpoints:
    alive_endpoint_dict[key] = target_endpoints[key]
# print(alive_endpoint_dict)

print(f"Found {len(alive_endpoint_dict)} alive endpoints, writing results...")
_s = get_interesting(alive_endpoint_dict).copy()

out_path = args.output + "unique_endpoints.txt"
endpoints = {'endpoints-parameters': alive_endpoint_dict}
with open(out_path, 'w') as f:
    f.write(json.dumps(endpoints))

