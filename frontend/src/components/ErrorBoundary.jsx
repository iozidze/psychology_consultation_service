import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="app-shell">
          <div className="panel">
            <p className="eyebrow">Ошибка интерфейса</p>
            <h1>Приложение не смогло отрисоваться</h1>
            <p className="runtime-error">{this.state.error.message}</p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
