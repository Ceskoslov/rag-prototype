export const LoadingIndicator = () => {
  return (
    <div
      aria-label="Loading"
      role="status"
      className="flex gap-1 items-center"
    >
      <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
      <div
        className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"
        style={{ animationDelay: '0.2s' }}
      />
      <div
        className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"
        style={{ animationDelay: '0.4s' }}
      />
    </div>
  )
}
