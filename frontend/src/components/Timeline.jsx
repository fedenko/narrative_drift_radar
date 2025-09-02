import React from 'react'

const eventTypeColors = {
  emergence: 'bg-green-100 text-green-800 border-green-200',
  shift: 'bg-blue-100 text-blue-800 border-blue-200',
  peak: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  decline: 'bg-red-100 text-red-800 border-red-200'
}

const eventTypeIcons = {
  emergence: '🌱',
  shift: '🔄',
  peak: '⭐',
  decline: '📉'
}

function Timeline({ events }) {
  if (!events || events.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-gray-400 text-lg mb-2">📊</div>
        <p className="text-gray-500">No timeline events available yet.</p>
        <p className="text-sm text-gray-400 mt-1">
          Run the data processing commands to generate narrative events.
        </p>
      </div>
    )
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <div className="space-y-4">
      {events.map((event, index) => (
        <div key={event.id || index} className="relative">
          {index !== events.length - 1 && (
            <div className="absolute left-4 top-12 w-0.5 h-16 bg-gray-200"></div>
          )}
          
          <div className="flex items-start space-x-4">
            <div className={`
              flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm
              ${eventTypeColors[event.event_type] || 'bg-gray-100 text-gray-800 border-gray-200'}
              border-2
            `}>
              {eventTypeIcons[event.event_type] || '📌'}
            </div>
            
            <div className="flex-grow min-w-0">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-gray-900">
                  {event.narrative?.name || 'Unknown Narrative'}
                </h3>
                <time className="text-xs text-gray-500">
                  {formatDate(event.event_date)}
                </time>
              </div>
              
              <div className="mt-1">
                <span className={`
                  inline-flex items-center px-2 py-1 rounded-full text-xs font-medium
                  ${eventTypeColors[event.event_type] || 'bg-gray-100 text-gray-800'}
                `}>
                  {event.event_type?.charAt(0).toUpperCase() + event.event_type?.slice(1) || 'Event'}
                </span>
                {event.significance_score && (
                  <span className="ml-2 text-xs text-gray-500">
                    Score: {event.significance_score.toFixed(2)}
                  </span>
                )}
              </div>
              
              <p className="mt-2 text-sm text-gray-600">
                {event.description}
              </p>
              
              {event.related_articles && event.related_articles.length > 0 && (
                <div className="mt-2">
                  <details className="text-xs text-gray-500">
                    <summary className="cursor-pointer hover:text-gray-700">
                      {event.related_articles.length} related articles
                    </summary>
                    <div className="mt-1 space-y-1">
                      {event.related_articles.slice(0, 3).map((article, idx) => (
                        <div key={idx} className="pl-2 border-l border-gray-200">
                          <a
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 underline"
                          >
                            {article.title}
                          </a>
                          <span className="ml-1 text-gray-400">({article.source})</span>
                        </div>
                      ))}
                    </div>
                  </details>
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default Timeline