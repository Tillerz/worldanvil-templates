// Cloudflare Worker
//
// Setup instructions see here: https://developers.cloudflare.com/learning-paths/workers/get-started/first-worker/

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const originalHostURL = 'https://www.worldanvil.com'
  const url = new URL(request.url)
  const apiEndpoint = url.pathname.replace('/proxy', '')
  const queryString = url.search
  
  const newUrl = `${originalHostURL}${apiEndpoint}${queryString}`
  const newRequest = new Request(newUrl, {
    method: request.method,
    headers: request.headers,
    body: request.body,
  })

  return fetch(newRequest)
}