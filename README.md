# Shakespeare Digital Variorum

A secure, AI-powered Shakespeare analysis tool that uses serverless functions to keep your API keys safe.

## Features

- 🔒 **Secure API Key Storage** - API keys are stored server-side, never exposed to the browser
- 🎭 **Advanced Shakespeare Analysis** - Multiple analysis levels from basic to expert
- 🤖 **Multiple AI Models** - Support for GPT-4o, GPT-4o Mini, GPT-4 Turbo, and GPT-3.5 Turbo
- 📱 **Responsive Design** - Works perfectly on desktop and mobile devices
- ⚡ **Fast Performance** - Serverless functions for quick responses

## Setup Instructions

### 1. Get Your OpenAI API Key

1. Visit [OpenAI's API page](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy the key (starts with `sk-`)

### 2. Deploy to Netlify

1. Push your code to GitHub
2. Connect your repository to Netlify
3. Set the environment variable:
   - **Variable name**: `OPENAI_API_KEY`
   - **Value**: Your OpenAI API key (e.g., `sk-...`)

### 3. Environment Variables

In your Netlify dashboard, go to **Site settings > Environment variables** and add:

```
OPENAI_API_KEY=sk-your-actual-api-key-here
APIBIBLE_KEY=your-api-bible-key-here
```

#### Optional: API Bible Integration

For enhanced Biblical allusion detection:

1. Visit [API.Bible](https://scripture.api.bible/) and sign up for a free account
2. Get your API key from the dashboard
3. Add `APIBIBLE_KEY` to your Netlify environment variables
4. The system will automatically search for Biblical references in Shakespeare text

## How It Works

1. **Frontend**: The HTML interface sends text analysis requests to the serverless function
2. **Serverless Function**: `functions/shakespeare.js` handles the OpenAI API calls securely
3. **API Key Security**: Your API key is stored as an environment variable and never exposed to the browser
4. **Response**: Analysis results are returned to the frontend and displayed to the user

## File Structure

```
├── index.html              # Main application interface
├── functions/
│   └── shakespeare.js      # Serverless function for API calls
├── netlify.toml           # Netlify configuration
├── package.json           # Dependencies
└── README.md             # This file
```

## Security Benefits

- ✅ API keys are never visible in browser developer tools
- ✅ No client-side API calls to OpenAI
- ✅ Environment variables are encrypted at rest
- ✅ Serverless functions run in isolated environments

## Usage

1. Select your preferred AI model
2. Choose the analysis level (Basic, Detailed, or Expert)
3. Paste Shakespeare text into the input area
4. Click "🔍 Analyze Text"
5. View the AI-powered analysis results

## Troubleshooting

- **"OpenAI API key not configured"**: Make sure you've set the `OPENAI_API_KEY` environment variable in Netlify
- **"Model not available"**: Check that your API key has access to the selected model
- **Connection errors**: Verify your Netlify deployment is working correctly

## Development

To test locally with Netlify CLI::

```bash
npm install -g netlify-cli
netlify dev
```

Make sure to set your environment variables in a `.env` file:

```
OPENAI_API_KEY=sk-your-api-key-here
```
