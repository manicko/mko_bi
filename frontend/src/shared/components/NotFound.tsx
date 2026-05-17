import { Link } from 'react-router-dom'

export function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center">
      <h1 className="text-6xl font-bold text-gray-800">404</h1>
      <p className="mt-4 text-lg text-gray-600">Page not found</p>
      <Link
        to="/dashboards"
        className="mt-6 text-blue-600 hover:text-blue-800 underline"
      >
        Go to Dashboards
      </Link>
    </div>
  )
}