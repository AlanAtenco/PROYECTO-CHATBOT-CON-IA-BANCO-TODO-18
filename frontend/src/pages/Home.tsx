import { AuthPayload } from '../api';
import Login from './Login';

interface HomeProps {
  onLogin: (auth: AuthPayload) => void;
}

export default function Home({ onLogin }: HomeProps) {
  return <Login onLogin={onLogin} />;
}
