import { Component, ErrorInfo, ReactNode } from 'react'
import { ErrorPage } from './ErrorPage'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    if (import.meta.env.DEV) {
      console.error('[ErrorBoundary]', error)
    } else {
      this.reportError(error, errorInfo.componentStack)
    }
  }

  private reportError(error: Error, componentStack: string | null): void {
    const payload = {
      error: { name: error.name, message: error.message, stack: error.stack },
      componentStack,
      url: window.location.href,
      userAgent: navigator.userAgent,
      timestamp: new Date().toISOString(),
    }
    fetch('/api/v1/client-errors', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }).catch(() => {})
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return <ErrorPage variant="500" error={this.state.error} />
    }
    return this.props.children
  }
}