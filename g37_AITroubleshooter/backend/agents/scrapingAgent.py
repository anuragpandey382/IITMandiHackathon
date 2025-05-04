import requests
from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin, urlparse
from langchain_text_splitters.markdown import MarkdownHeaderTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

BASE_URL = "https://in.mathworks.com"
START_PATH = "/help/slrealtime/ug/troubleshooting-basics.html"
MAX_PAGES = 250  # stop after visiting 150 unique pages

visited = set()
pages_to_visit = []
all_texts = []  # tuples (url, markdown_content)

# Initialize open-source embedder and header-based splitter
embedder = HuggingFaceEmbeddings(
    model_name="BAAI/bge-base-en-v1.5",
    model_kwargs={"device": "cpu"}
)
splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("##", "H2"), ("###", "H3")],
    strip_headers=False,
)

# Crawler functions
def fetch_soup(url: str) -> BeautifulSoup:
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")
    except Exception as e:
        logging.warning(f"Failed to fetch {url}: {e}")
        return None


def extract_page_markdown(soup: BeautifulSoup) -> str:
    """
    Convert main content sections to Markdown,
    preserving header hierarchy.
    """
    content_secs = soup.find_all("section", {"itemprop": "content"})
    md_lines = []

    def walk(node):
        if not isinstance(node, Tag):
            return
        if node.name in ("h2", "h3", "h4"):
            level = int(node.name[1])
            md_lines.append(f"{'#'*level} {node.get_text(' ', strip=True)}")
        elif node.name == "p":
            md_lines.append(node.get_text(' ', strip=True))
        elif node.name == "li":
            md_lines.append(f"- {node.get_text(' ', strip=True)}")
        elif node.name == "pre":
            md_lines.append("```\n" + node.get_text(strip=True) + "\n```")
        for child in node.children:
            walk(child)

    for sec in content_secs:
        walk(sec)

    return "\n\n".join(md_lines)

def find_related_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Extract links under 'Related Topics' or 'See Also' sections."""
    related = []
    
    for header in soup.find_all(string=re.compile(r"^(Related Topics|See Also)$", re.I)):
        header_tag = header if isinstance(header, Tag) else header.parent
        block = header_tag.find_next_sibling(lambda tag: tag.name in ['ul', 'div', 'section'])
        if not block:
            continue
        for a in block.find_all('a', href=True):
            full = urljoin(base_url, a['href'])
            parsed = urlparse(full)
            if parsed.netloc.endswith('mathworks.com'):
                clean = parsed.scheme + '://' + parsed.netloc + parsed.path
                if clean not in visited and clean not in related:
                    related.append(clean)
    return related

def find_all_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Extract all in-domain documentation links (anchors) from main content."""
    links = []
    
    for sec in soup.find_all("section", {"itemprop": "content"}):
        for a in sec.find_all('a', href=True):
            full = urljoin(base_url, a['href'])
            parsed = urlparse(full)
            if parsed.netloc.endswith('mathworks.com'):
                clean = parsed.scheme + '://' + parsed.netloc + parsed.path
                if clean not in links:
                    links.append(clean)
    return links

# Begin crawl
start_url = urljoin(BASE_URL, START_PATH)
pages_to_visit.append(start_url)

while pages_to_visit and len(visited) < MAX_PAGES:
    url = pages_to_visit.pop(0)
    if url in visited:
        continue
    logging.info(f"Visiting: {url}")
    visited.add(url)

    soup = fetch_soup(url)
    if not soup:
        continue

    # Extract markdown
    md = extract_page_markdown(soup)
    # Extract links: all anchors only for first page; otherwise empty
    page_links = []
    if url == start_url:
        page_links = find_all_links(soup, start_url)
        pages_to_visit.extend(page_links)
    # Enqueue only related/see also links for recursion
    for link in find_related_links(soup, url):
        if link not in visited:
            pages_to_visit.append(link)

    all_texts.append((url, md, page_links))

logging.info(f"Crawled {len(visited)} pages (limit {MAX_PAGES}).")
with open("visited.txt", "w") as vf:
    for link in visited:
        vf.write(link + "\n")
logging.info("Saved visited URLs to visited.txt")

# Chunk, embed, and store metadata
from langchain.schema import Document
chunks = []
for url, md, links in all_texts:
    docs = splitter.split_text(md)
    for doc in docs:
        heading = doc.metadata.get('header', 'Unknown')
        metadata = {"source": url, "heading": heading}
        if links:
            metadata["links"] = links
        chunks.append(Document(page_content=doc.page_content, metadata=metadata))

logging.info(f"Prepared {len(chunks)} chunks with metadata.")

# Build and persist FAISS store
db = FAISS.from_documents(chunks, embedder)
out_dir = "backend/faiss_vector_store"
db.save_local(out_dir)
logging.info(f"Saved FAISS vector store to {out_dir}")
print("Done building vector store with correct metadata!")