import axios from 'axios'

const api = axios.create({ baseURL: '', withCredentials: true })

// request adds Authorization header if token present
api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('token')
  if(token) cfg.headers['Authorization'] = `Bearer ${token}`
  return cfg
})

let isRefreshing = false
let refreshQueue = []

function processQueue(err, token = null){
  refreshQueue.forEach(p => { if(err) p.reject(err); else p.resolve(token) })
  refreshQueue = []
}

api.interceptors.response.use(undefined, async err => {
  const originalReq = err.config
  if(err.response && err.response.status === 401 && !originalReq._retry){
    originalReq._retry = true
    // refresh token is stored in an HttpOnly cookie set by server
    // if no cookie present, backend will reject refresh request

    if(isRefreshing){
      return new Promise((resolve, reject) => {
        refreshQueue.push({ resolve, reject })
      }).then(token => {
        originalReq.headers['Authorization'] = `Bearer ${token}`
        return api(originalReq)
      })
    }

    isRefreshing = true
    try{
      const r = await axios.post('/api/token/refresh', {}, { withCredentials: true })
      const newToken = r.data.access_token
      localStorage.setItem('token', newToken)
      processQueue(null, newToken)
      originalReq.headers['Authorization'] = `Bearer ${newToken}`
      return api(originalReq)
    }catch(e){
      processQueue(e, null)
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      window.location.href = '/login'
      return Promise.reject(e)
    }finally{
      isRefreshing = false
    }
  }
  return Promise.reject(err)
})

export default api
