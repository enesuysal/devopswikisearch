import os
import re
import markdown
import datetime
import urllib.parse
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch

# Connect to ElasticSearch (Assuming it's running locally on default port 9200)
es = Elasticsearch(['http://127.0.0.1:9200'])


# Define the index name
index_name = "wiki_pages"

# Define the mapping for the index
mapping = {
    "settings": {
        "number_of_shards": 1,    # Number of shards for scalability
        "number_of_replicas": 0   # Number of replicas for fault tolerance
    },
    "mappings": {
        "properties": {
            "title": {
                "type": "text"   # Use text type for full-text search
            },
            "content": {
                "type": "text"   # This will contain the full wiki page content
            },
            "url": {
                "type": "keyword"   # Use keyword type to store URLs
            },
            "category": {
                "type": "keyword"   # Category can be used for filtering and categorization
            },
            "tags": {
                "type": "keyword"   # Tags for filtering, don't need to analyze
            },
            "created_at": {
                "type": "date"      # Store the date the wiki page was created
            }
        }
    }
}
# Directory containing the markdown files
input_directory = './'

# Regex to capture category and tags
category_pattern = re.compile(r'\*\*Category:\*\*\s*(.+)')
tags_pattern = re.compile(r'\*\*Tags:\*\*\s*(.+)')

# Function to extract inline metadata

# Function to clean file names


def clean_file_name(name):
    if name.startswith("./"):
        name = name[2:]  # Remove './' from the beginning
    if name.endswith(".md"):
        name = name[:-3]  # Remove '.md' from the end
    return encode_special_chars(name)


def encode_special_chars(input_string):
    return urllib.parse.quote(input_string)


def extract_inline_metadata(content):
    category_match = category_pattern.search(content)
    tags_match = tags_pattern.search(content)

    category = category_match.group(1) if category_match else 'Uncategorized'
    tags = tags_match.group(1).split() if tags_match else []
    tags = [tag.lstrip('#') for tag in tags]  # Remove leading hashtags

    return category, tags


# Check if the index already exists
if not es.indices.exists(index=index_name):
    # Create the index with the defined mapping
    es.indices.create(index=index_name, body=mapping)
    print(f"Index '{index_name}' created successfully!")
else:
    print(f"Index '{index_name}' already exists.")

# Walk through the input directory and all its subdirectories
for dirpath, _, filenames in os.walk(input_directory):
    for filename in filenames:
        if filename.endswith('.md'):
            file_path = os.path.join(dirpath, filename)

            # Read the markdown file
            with open(file_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            # Extract inline metadata (category and tags)
            category, tags = extract_inline_metadata(markdown_content)
            # Convert markdown to HTML and strip HTML tags
            html_content = markdown.markdown(markdown_content)
            soup = BeautifulSoup(html_content, 'html.parser')
            plain_text = soup.get_text()

            # print(f'{plain_text}')
            # Example wiki page data
            wiki_page = {
                "title": filename,
                "content": plain_text,
                "url": "https://dev.azure.com/dynamicscrm/Solutions/_wiki/wikis/DTP%20Solutions.wiki?pagePath=%2F" + clean_file_name(file_path),
                "category": category,
                "tags": tags,
                "created_at": datetime.datetime.now()
            }

            # Insert the document into the 'wiki_pages' index
            response = es.index(index=index_name, document=wiki_page)

            # Print the response to confirm the document has been indexed
            # print(f"Document indexed: {response['_id']}")


# Search for documents where the content contains the word "Ansible"
search_query = {
    "query": {
        "match": {
            "content": "Microsoft Fabric goals"
        }
    }
}

# Execute the search query
response = es.search(index=index_name, body=search_query)

# Print search results
for hit in response['hits']['hits']:
    print(f"Title: {hit['_source']['title']}")
    print(f"Content: {hit['_source']['content']}")
    print(f"URL: {hit['_source']['url']}")
    print('-' * 50)

# Delete the index if you want to start over
es.indices.delete(index=index_name)
print(f"Index '{index_name}' deleted.")
