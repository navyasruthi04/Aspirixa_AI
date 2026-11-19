import { useCallback, useEffect, useState } from 'react';

// Runs an API function and gives back: status (loading | success | error), data, error, reload
export function useAsync(fn) {
  const [state, setState] = useState({ status: 'loading', data: null, error: null });

  const run = useCallback(() => {
    setState({ status: 'loading', data: null, error: null });
    fn()
      .then((data) => setState({ status: 'success', data, error: null }))
      .catch((err) => setState({ status: 'error', data: null, error: err.message }));
  }, [fn]);

  useEffect(() => { run(); }, [run]);
  return { ...state, reload: run };
}