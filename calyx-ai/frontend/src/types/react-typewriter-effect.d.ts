declare module 'react-typewriter-effect' {
  import * as React from 'react';
  interface TypewriterProps {
    text: string;
    typeSpeed?: number;
    cursorColor?: string;
    startDelay?: number;
    [key: string]: any;
  }
  const Typewriter: React.FC<TypewriterProps>;
  export default Typewriter;
}
