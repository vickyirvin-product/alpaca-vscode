import { Link } from 'react-router-dom';
import alpacaLogo from '@/assets/alpaca-logo-stacked.svg';

interface LogoProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl';
}

const sizeClasses = {
  xs: 'h-10',
  sm: 'h-24',
  md: 'h-40',
  lg: 'h-56',
  xl: 'h-72',
  '2xl': 'h-96',
};

export function Logo({ size = 'md' }: LogoProps) {
  return (
    <Link to="/" className="flex items-center justify-center">
      <img 
        src={alpacaLogo} 
        alt="Alpaca Logo" 
        className={`${sizeClasses[size]} object-contain`}
      />
    </Link>
  );
}
