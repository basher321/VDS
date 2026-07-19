export default function VdsMark({ size = 42 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48">
      <rect width="48" height="48" rx="11" fill="#0b2f6b" />
      <rect x="4" y="4" width="40" height="40" rx="8" fill="none" stroke="#0fb5a5" strokeWidth="1.5" opacity="0.5" />
      <text x="24" y="30" fontFamily="Inter,sans-serif" fontSize="15" fontWeight="700" fill="#fff" textAnchor="middle" letterSpacing="1">VDS</text>
    </svg>
  );
}
