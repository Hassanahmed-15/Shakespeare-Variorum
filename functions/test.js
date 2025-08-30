exports.handler = async (event, context) => {
  return {
    statusCode: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: 'Netlify function is working!',
      timestamp: new Date().toISOString(),
      method: event.httpMethod,
      path: event.path
    })
  }
}
