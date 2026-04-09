defmodule WorkOrderService.Router do
  use Plug.Router
  require Logger

  plug Plug.Parsers,
    parsers: [:json],
    json_decoder: Jason

  plug :match
  plug :dispatch

  # List all work orders (with pagination)
  get "/api/work-orders" do
    conn = fetch_query_params(conn)
    page = String.to_integer(conn.params["page"] || "1")
    limit = String.to_integer(conn.params["limit"] || "20")
    orders = WorkOrderService.Store.all()
    total = length(orders)
    offset = (page - 1) * limit
    results = orders |> Enum.drop(offset) |> Enum.take(limit)

    send_json(conn, 200, %{
      workOrders: results,
      total: total,
      page: page,
      limit: limit,
      totalPages: div(total + limit - 1, limit)
    })
  end

  # Get work order stats
  get "/api/work-orders/stats" do
    send_json(conn, 200, WorkOrderService.Store.stats())
  end

  # Health check (must be before :id route)
  get "/api/work-orders/health" do
    send_json(conn, 200, %{
      status: "Healthy",
      service: "work-order-service",
      language: "Elixir",
      timestamp: DateTime.utc_now() |> DateTime.to_iso8601()
    })
  end

  # Get single work order
  get "/api/work-orders/:id" do
    case WorkOrderService.Store.get(id) do
      nil -> send_json(conn, 404, %{error: "Work order not found"})
      order ->
        # Call customer-service to enrich with site info (adds trace hop)
        customer_url = System.get_env("CUSTOMER_SERVICE_URL") || "http://customer-service:4567"
        customer_info = case HTTPoison.get("#{customer_url}/api/customers/region/#{URI.encode(order.region)}", [], recv_timeout: 5000) do
          {:ok, %{status_code: 200, body: body}} -> Jason.decode!(body)
          _ -> nil
        end
        send_json(conn, 200, Map.put(order, :customerContext, customer_info))
    end
  end

  # Create work order
  post "/api/work-orders" do
    order = WorkOrderService.Store.create(conn.body_params)
    Logger.info("Work order created: #{order.id}")

    # Notify audit service (adds trace hop)
    audit_url = System.get_env("AUDIT_SERVICE_URL") || "http://audit-service:8090"
    HTTPoison.post(
      "#{audit_url}/api/audit/log",
      Jason.encode!(%{eventType: "work_order.created", source: "work-order-service", action: "CREATE", details: %{workOrderId: order.id, outageId: order.outageId}}),
      [{"Content-Type", "application/json"}],
      recv_timeout: 3000
    ) |> case do
      {:ok, _} -> :ok
      {:error, _} -> Logger.warn("Failed to notify audit service")
    end

    send_json(conn, 201, order)
  end

  # Update work order
  put "/api/work-orders/:id" do
    case WorkOrderService.Store.update(id, conn.body_params) do
      nil -> send_json(conn, 404, %{error: "Work order not found"})
      updated ->
        Logger.info("Work order updated: #{id}")
        send_json(conn, 200, updated)
    end
  end

  match _ do
    send_json(conn, 404, %{error: "Not found"})
  end

  defp send_json(conn, status, body) do
    conn
    |> put_resp_content_type("application/json")
    |> send_resp(status, Jason.encode!(body))
  end
end
