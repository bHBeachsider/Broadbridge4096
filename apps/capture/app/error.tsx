"use client";
export default function ErrorPage({ reset }: { reset: () => void }) {
  return <main><h1>Unable to load this page</h1><p>Please try again. If the problem continues, contact Brad.</p><button className="btn" onClick={reset}>Try again</button></main>;
}
