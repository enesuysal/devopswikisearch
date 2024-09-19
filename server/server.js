// server.js
const express = require('express');
const axios = require('axios');
const { Client } = require('@elastic/elasticsearch');
require('dotenv').config();

const app = express();
const port = 5000;
// ADD THIS
var cors = require('cors');
app.use(cors());
app.use(express.json());

// Initialize Elasticsearch client
const esClient = new Client({ node: 'http://127.0.0.1:9200' });

// ChatGPT API credentials
const OPENAI_API_KEY = 'YOUR_OPENAI';

// Function to send a message to ChatGPT API
const queryChatGPT = async (message) => {
  const apiUrl = 'https://api.openai.com/v1/chat/completions';
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${OPENAI_API_KEY}`,
  };

  const data = {
    model: 'gpt-3.5-turbo', // or 'gpt-3.5-turbo'
    messages: [{ role: 'user', content: message }],
    max_tokens: 150,
    temperature: 0.7,
  };

  try {
    const response = await axios.post(apiUrl, data, { headers });
    return response.data.choices[0].message.content;
  } catch (error) {
    console.error('Error querying ChatGPT:', error);
    throw new Error('Failed to get response from ChatGPT');
  }
    console.log("data", data);
};

// Function to search Elasticsearch
const searchElasticsearch = (query) => {
    console.log("searching for: ", query);
    return query.hits.hits.map((hit) => ({
        title: hit._source.title,
        content: hit._source.content,
        link: hit._source.url, // Assuming you have a link field in Elasticsearch
        }));
};

// Endpoint for receiving user queries
app.post('/ask', async (req, res) => {
  console.log('Received question:', req.body.question);
  const userQuestion = req.body.question;

  try {
    // Step 1: Analyze the question with ChatGPT
    const analysis = await queryChatGPT(
      `Analyze the following question for key search terms: ${userQuestion}`
    );
    console.log('Analysis:', analysis);
    
  try {
    const search_query = {
        "query": {
          "multi_match": {
            "query": analysis,
            "fields": ['title', 'content'], // Fields you indexed in Elasticsearch
            }
        }
        };

    await esClient.search({
      index: 'wiki_pages', // your Elasticsearch index name
      body: search_query,
    }).then(response => {
        console.log("response", response.hits.hits);
        const searchResults = searchElasticsearch(response);

        // Step 3: Summarize the Elasticsearch results using ChatGPT
        queryChatGPT(`Summarize the following content: ${JSON.stringify(searchResults.map(result => result.content))}`).then(summary => {
            console.log("summary", summary);
                const response = {
                    summary: summary,
                    links: searchResults.map((result) => ({ title: result.title, link: result.link })),
                    };
                res.json(response);

        }).catch(error => {
            console.log(error);
        }
        );
         
    }).catch(error => {
        console.log(error);
    }
    );

  } catch (error) {
    console.error('Error searching Elasticsearch:', error);
    throw new Error('Failed to search Elasticsearch');
  }
 

    // const response = {
  } catch (error) {
    console.error('Error processing the request:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.listen(port, () => {
  console.log(`Server is running on http://localhost:${port}`);
});
