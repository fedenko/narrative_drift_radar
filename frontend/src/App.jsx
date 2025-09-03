import React, { useState, useEffect } from 'react'
import axios from 'axios'
import Timeline from './components/Timeline'

const API_BASE = 'http://localhost:8000/api'

function App() {
  const [timelineData, setTimelineData] = useState([])
  const [narratives, setNarratives] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState(null)
  const [timelinePagination, setTimelinePagination] = useState({
    currentPage: 1,
    totalPages: 1,
    hasNext: false,
    hasPrevious: false,
    totalCount: 0
  })

  const fetchTimelineData = async (page = 1, append = false) => {
    try {
      if (!append) setLoading(true)
      else setLoadingMore(true)
      
      const timelineRes = await axios.get(`${API_BASE}/timeline/?page=${page}`)
      const timelineResponse = timelineRes.data
      
      const newEvents = timelineResponse.results || []
      
      if (append) {
        setTimelineData(prev => [...prev, ...newEvents])
      } else {
        setTimelineData(newEvents)
      }
      
      // Update pagination info
      setTimelinePagination({
        currentPage: page,
        totalPages: Math.ceil(timelineResponse.count / 20),
        hasNext: !!timelineResponse.next,
        hasPrevious: !!timelineResponse.previous,
        totalCount: timelineResponse.count || 0
      })
      
      setError(null)
    } catch (err) {
      setError('Failed to fetch timeline data. Make sure the backend is running.')
      console.error('Error fetching timeline data:', err)
    } finally {
      setLoading(false)
      setLoadingMore(false)
    }
  }

  const fetchNarratives = async () => {
    try {
      const narrativesRes = await axios.get(`${API_BASE}/narratives/`)
      setNarratives(narrativesRes.data.results || narrativesRes.data)
    } catch (err) {
      console.error('Error fetching narratives:', err)
    }
  }

  useEffect(() => {
    const fetchData = async () => {
      await Promise.all([
        fetchTimelineData(1),
        fetchNarratives()
      ])
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading narrative data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">Error</div>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Narrative Drift Radar</h1>
          <p className="text-gray-600 mt-1">Tracking narrative shifts in real-time</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Narrative Timeline</h2>
                {timelinePagination.totalCount > 0 && (
                  <span className="text-sm text-gray-500">
                    {timelinePagination.totalCount} total events
                  </span>
                )}
              </div>
              <Timeline 
                events={timelineData} 
                pagination={timelinePagination}
                onLoadMore={() => fetchTimelineData(timelinePagination.currentPage + 1, true)}
                loadingMore={loadingMore}
              />
            </div>
          </div>
          
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Narratives</h3>
              {narratives.length === 0 ? (
                <p className="text-gray-500 text-sm">No active narratives found.</p>
              ) : (
                <div className="space-y-3">
                  {narratives.slice(0, 5).map((narrative) => (
                    <div key={narrative.id} className="border-l-4 border-blue-500 pl-3">
                      <h4 className="font-medium text-gray-900">{narrative.name}</h4>
                      <p className="text-sm text-gray-600 mt-1">{narrative.description}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App