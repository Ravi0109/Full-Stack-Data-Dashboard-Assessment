type StatusMessageProps = {
  state: 'loading' | 'empty' | 'error';
  title: string;
  detail?: string;
};

export function StatusMessage({ state, title, detail }: StatusMessageProps) {
  return (
    <div className={`status-message ${state}`} role={state === 'error' ? 'alert' : 'status'}>
      <strong>{title}</strong>
      {detail ? <span>{detail}</span> : null}
    </div>
  );
}
