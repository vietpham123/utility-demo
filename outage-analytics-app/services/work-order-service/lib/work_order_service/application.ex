defmodule WorkOrderService.Application do
  @moduledoc """
  Work Order Service (Elixir/Plug) — Manages repair work orders
  Adds Elixir to polyglot mix (like AstroShop's flagd-ui service)
  Called by crew-dispatch-service after dispatch, calls customer-service for site info
  """
  use Application
  require Logger

  @impl true
  def start(_type, _args) do
    Logger.info("Work Order Service (Elixir) starting on port 4000")

    children = [
      {WorkOrderService.Store, []},
      {Plug.Cowboy, scheme: :http, plug: WorkOrderService.Router, options: [port: 4000]}
    ]

    opts = [strategy: :one_for_one, name: WorkOrderService.Supervisor]
    Supervisor.start_link(children, opts)
  end
end
