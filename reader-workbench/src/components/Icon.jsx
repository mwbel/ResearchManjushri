const paths = {
  library: (
    <>
      <path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3V4z" />
      <path d="M8 17h11" />
      <path d="M8 4v13" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="6" />
      <path d="m16 16 4 4" />
    </>
  ),
  translate: (
    <>
      <path d="M4 5h9" />
      <path d="M9 3v2" />
      <path d="M6 9c1.2 2 2.8 3.5 5 4.5" />
      <path d="M12 5c-.5 3.4-2.6 6.1-6 8" />
      <path d="M14 20l4-9 4 9" />
      <path d="M16 16h4" />
    </>
  ),
  spark: (
    <>
      <path d="M12 3l1.7 5.2L19 10l-5.3 1.8L12 17l-1.7-5.2L5 10l5.3-1.8L12 3z" />
      <path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z" />
    </>
  ),
  save: (
    <>
      <path d="M5 4h11l3 3v13H5V4z" />
      <path d="M8 4v6h8" />
      <path d="M8 20v-6h8v6" />
    </>
  ),
  note: (
    <>
      <path d="M6 4h12v16H6V4z" />
      <path d="M9 8h6" />
      <path d="M9 12h6" />
      <path d="M9 16h4" />
    </>
  ),
  sync: (
    <>
      <path d="M17 3l4 4-4 4" />
      <path d="M3 7h18" />
      <path d="M7 21l-4-4 4-4" />
      <path d="M3 17h18" />
    </>
  ),
  export: (
    <>
      <path d="M12 3v12" />
      <path d="m7 8 5-5 5 5" />
      <path d="M5 15v5h14v-5" />
    </>
  ),
  plus: (
    <>
      <path d="M12 5v14" />
      <path d="M5 12h14" />
    </>
  ),
};

export default function Icon({ name, size = 18 }) {
  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {paths[name]}
    </svg>
  );
}
