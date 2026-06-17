import React from 'react'
import ReactDOM from 'react-dom/client'
import { App } from './app/providers'
import { validateEnv } from './shared/config/env'

// Validate environment variables before app initialization
validateEnv()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
