import React from 'react'
import { useTranslation } from 'react-i18next'

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

function Timeline({ events, pagination, onLoadMore, loadingMore }) {
  const { t, i18n } = useTranslation()
  if (!events || events.length === 0) {
    return (
      <div className="text-center py-8">
        <div className="text-gray-400 text-lg mb-2">📊</div>
        <p className="text-gray-500">{t('No timeline events available yet.')}</p>
        <p className="text-sm text-gray-400 mt-1">
          {t('Run the data processing commands to generate narrative events.')}
        </p>
      </div>
    )
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    const locale = i18n.language === 'uk' ? 'uk-UA' : 'en-US'
    return date.toLocaleDateString(locale, {
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
                  {event.event_type ? t(`Narrative ${event.event_type.charAt(0).toUpperCase() + event.event_type.slice(1)}`) : t('Event')}
                </span>
                {event.significance_score && (
                  <span className="ml-2 text-xs text-gray-500">
                    {t('Score')}: {event.significance_score.toFixed(2)}
                  </span>
                )}
              </div>
              
              <p className="mt-2 text-sm text-gray-600">
                {event.description}
              </p>

              {/* Quality Metrics */}
              {event.narrative && (
                <div className="mt-3 flex flex-wrap gap-4 text-xs">
                  {event.narrative.source_diversity_score !== undefined && (
                    <div className="flex items-center space-x-1">
                      <span className="inline-block w-2 h-2 bg-blue-500 rounded-full"></span>
                      <span className="font-medium">{t('Diversity')}:</span>
                      <span className="text-gray-600">{(event.narrative.source_diversity_score * 100).toFixed(0)}%</span>
                    </div>
                  )}
                  {event.narrative.unique_sources_count !== undefined && (
                    <div className="flex items-center space-x-1">
                      <span className="inline-block w-2 h-2 bg-green-500 rounded-full"></span>
                      <span className="font-medium">{t('Sources')}:</span>
                      <span className="text-gray-600">{event.narrative.unique_sources_count}</span>
                    </div>
                  )}
                  {event.narrative.coherence_score !== undefined && (
                    <div className="flex items-center space-x-1">
                      <span className="inline-block w-2 h-2 bg-purple-500 rounded-full"></span>
                      <span className="font-medium">{t('Coherence')}:</span>
                      <span className="text-gray-600">{(event.narrative.coherence_score * 100).toFixed(0)}%</span>
                    </div>
                  )}
                  {event.narrative.support_count !== undefined && (
                    <div className="flex items-center space-x-1">
                      <span className="inline-block w-2 h-2 bg-orange-500 rounded-full"></span>
                      <span className="font-medium">{t('Support')}:</span>
                      <span className="text-gray-600">{event.narrative.support_count}</span>
                    </div>
                  )}
                </div>
              )}
              
              {event.related_articles && event.related_articles.length > 0 && (
                <div className="mt-3">
                  <details className="text-xs text-gray-500">
                    <summary className="cursor-pointer hover:text-gray-700 flex items-center space-x-1">
                      <span>{event.related_articles.length} {t('related articles')}</span>
                      {event.narrative?.unique_sources_count && (
                        <span className="text-gray-400">{t('from')} {event.narrative.unique_sources_count} {t('sources')}</span>
                      )}
                    </summary>
                    <div className="mt-2 space-y-2">
                      {event.related_articles.slice(0, 5).map((article, idx) => (
                        <div key={idx} className="pl-3 border-l-2 border-gray-200 bg-gray-50 p-2 rounded">
                          <a
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-800 underline text-sm font-medium block"
                          >
                            {article.title}
                          </a>
                          <div className="flex items-center justify-between mt-1">
                            <span className="text-gray-500 text-xs">{article.source}</span>
                            <span className="text-gray-400 text-xs">
                              {new Date(article.published_date).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                      ))}
                      {event.related_articles.length > 5 && (
                        <p className="text-xs text-gray-400 pl-3">
                          {t('...and')} {event.related_articles.length - 5} {t('more articles')}
                        </p>
                      )}
                    </div>
                  </details>
                </div>
              )}
            </div>
          </div>
        </div>
      ))}
      
      {/* Pagination Controls */}
      {pagination && pagination.totalPages > 1 && (
        <div className="mt-8 pt-6 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {t('Showing')} {events.length} {t('of')} {pagination.totalCount} {t('events')}
              {pagination.currentPage > 1 && (
                <span> ({t('Page')} {pagination.currentPage} {t('of')} {pagination.totalPages})</span>
              )}
            </div>
            
            <div className="flex space-x-2">
              {pagination.hasNext && (
                <button
                  onClick={onLoadMore}
                  disabled={loadingMore}
                  className="px-4 py-2 text-sm font-medium text-blue-600 bg-white border border-blue-600 rounded-md hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loadingMore ? (
                    <span className="flex items-center">
                      <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      {t('Loading...')}
                    </span>
                  ) : (
                    t('Load More Events')
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Timeline