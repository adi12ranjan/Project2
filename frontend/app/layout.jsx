import './globals.css';
import Shell from '../components/Shell';

export const metadata = {
  title: 'TraceMail AI — Email Threat & Forensic Intelligence',
  description: 'AI-Powered Email Threat Detection & Forensic Intelligence Platform',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
