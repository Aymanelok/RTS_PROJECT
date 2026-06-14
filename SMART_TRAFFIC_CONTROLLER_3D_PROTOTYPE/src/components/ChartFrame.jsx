import { useEffect, useRef, useState } from 'react';

export default function ChartFrame({ className = '', children }) {
  const frameRef = useRef(null);
  const [size, setSize] = useState(null);

  useEffect(() => {
    const element = frameRef.current;
    if (!element) return undefined;

    const updateSize = () => {
      const rect = element.getBoundingClientRect();
      const width = Math.round(rect.width);
      const height = Math.round(rect.height);
      if (width > 0 && height > 0) {
        setSize((previous) =>
          previous?.width === width && previous?.height === height ? previous : { width, height },
        );
      }
    };

    updateSize();

    if (window.ResizeObserver) {
      const observer = new ResizeObserver(updateSize);
      observer.observe(element);
      return () => observer.disconnect();
    }

    window.addEventListener('resize', updateSize);
    return () => window.removeEventListener('resize', updateSize);
  }, []);

  return (
    <div ref={frameRef} className={className}>
      {size ? children(size) : null}
    </div>
  );
}
