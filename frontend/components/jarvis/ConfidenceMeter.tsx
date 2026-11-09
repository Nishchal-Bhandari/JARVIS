export function ConfidenceMeter({ confidence }: { confidence: number }) {
  const filled = Math.round(confidence * 10);
  return (
    <div className="flex items-center gap-3" aria-label={`Confidence ${Math.round(confidence * 100)} percent`}>
      <div className="flex gap-1" role="img" aria-label={`${Math.round(confidence * 100)}% confidence`}>
        {Array.from({ length: 10 }, (_, i) => (
          <span key={i} className={`h-4 w-2 rounded-sm ${i < filled ? "bg-cause" : "bg-border"}`} />
        ))}
      </div>
      <span className="tabular text-2xl font-bold">{Math.round(confidence * 100)}%</span>
    </div>
  );
}
