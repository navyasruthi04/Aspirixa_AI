import Card from './Card.jsx';

export default function ChartCard({ title, subtitle, children }) {
  return <Card title={title} subtitle={subtitle} className="hover">{children}</Card>;
}