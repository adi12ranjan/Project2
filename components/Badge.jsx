export default function Badge({ classification, size }) {
  const cls = (classification || '').toLowerCase().replace(' ', '-');
  const style = size === 'sm' ? { padding: '4px 10px', fontSize: '9.5px' } : {};
  return (
    <span className={`badge ${cls}`} style={style}>
      {classification}
    </span>
  );
}
