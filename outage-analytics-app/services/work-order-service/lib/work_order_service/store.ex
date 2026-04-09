defmodule WorkOrderService.Store do
  @moduledoc "In-memory work order store using Agent"
  use Agent

  @work_types ["repair", "inspection", "maintenance", "emergency", "vegetation", "equipment_replacement"]
  @priorities ["critical", "high", "medium", "low"]
  @statuses ["open", "assigned", "in_progress", "on_hold", "completed", "cancelled"]
  @regions ["Chicago-Metro", "Baltimore-Metro", "Philadelphia-Metro", "DC-Metro", "Atlantic-Coast", "Delaware-Valley"]

  def start_link(_opts) do
    Agent.start_link(fn -> generate_initial_orders() end, name: __MODULE__)
  end

  def all do
    Agent.get(__MODULE__, & &1)
  end

  def get(id) do
    Agent.get(__MODULE__, fn orders -> Enum.find(orders, &(&1.id == id)) end)
  end

  def create(params) do
    order = %{
      id: "WO-#{:rand.uniform(9999) |> Integer.to_string() |> String.pad_leading(4, "0")}",
      outageId: params["outageId"],
      type: params["type"] || Enum.random(@work_types),
      priority: params["priority"] || "medium",
      status: "open",
      region: params["region"] || Enum.random(@regions),
      description: params["description"] || "Work order created",
      assignedCrew: nil,
      estimatedHours: params["estimatedHours"] || :rand.uniform(8),
      actualHours: nil,
      createdAt: DateTime.utc_now() |> DateTime.to_iso8601(),
      updatedAt: DateTime.utc_now() |> DateTime.to_iso8601(),
      completedAt: nil,
      notes: []
    }

    Agent.update(__MODULE__, fn orders -> [order | orders] end)
    order
  end

  def update(id, params) do
    Agent.get_and_update(__MODULE__, fn orders ->
      case Enum.find_index(orders, &(&1.id == id)) do
        nil -> {nil, orders}
        idx ->
          old = Enum.at(orders, idx)
          updated = Map.merge(old, %{
            status: params["status"] || old.status,
            assignedCrew: params["assignedCrew"] || old.assignedCrew,
            actualHours: params["actualHours"] || old.actualHours,
            completedAt: if(params["status"] == "completed", do: DateTime.utc_now() |> DateTime.to_iso8601(), else: old.completedAt),
            updatedAt: DateTime.utc_now() |> DateTime.to_iso8601(),
            notes: old.notes ++ if(params["note"], do: [%{text: params["note"], timestamp: DateTime.utc_now() |> DateTime.to_iso8601()}], else: [])
          })
          new_orders = List.replace_at(orders, idx, updated)
          {updated, new_orders}
      end
    end)
  end

  def stats do
    orders = all()
    %{
      total: length(orders),
      byStatus: Enum.group_by(orders, & &1.status) |> Enum.map(fn {k, v} -> {k, length(v)} end) |> Map.new(),
      byPriority: Enum.group_by(orders, & &1.priority) |> Enum.map(fn {k, v} -> {k, length(v)} end) |> Map.new(),
      byType: Enum.group_by(orders, & &1.type) |> Enum.map(fn {k, v} -> {k, length(v)} end) |> Map.new(),
      byRegion: Enum.group_by(orders, & &1.region) |> Enum.map(fn {k, v} -> {k, length(v)} end) |> Map.new(),
      openOrders: Enum.count(orders, &(&1.status in ["open", "assigned", "in_progress"])),
      completedOrders: Enum.count(orders, &(&1.status == "completed")),
      avgEstimatedHours: if(length(orders) > 0, do: Float.round(Enum.sum(Enum.map(orders, & &1.estimatedHours)) / length(orders), 1), else: 0)
    }
  end

  defp generate_initial_orders do
    for i <- 1..30 do
      status = Enum.random(@statuses)
      %{
        id: "WO-#{Integer.to_string(i) |> String.pad_leading(4, "0")}",
        outageId: "OUT-#{Integer.to_string(:rand.uniform(50)) |> String.pad_leading(3, "0")}",
        type: Enum.random(@work_types),
        priority: Enum.random(@priorities),
        status: status,
        region: Enum.random(@regions),
        description: "#{Enum.random(@work_types) |> String.replace("_", " ") |> String.capitalize()} for #{Enum.random(@regions)}",
        assignedCrew: if(status in ["assigned", "in_progress", "completed"], do: "Crew-#{:rand.uniform(8)}", else: nil),
        estimatedHours: :rand.uniform(8),
        actualHours: if(status == "completed", do: :rand.uniform(10), else: nil),
        createdAt: DateTime.utc_now() |> DateTime.add(-:rand.uniform(72) * 3600) |> DateTime.to_iso8601(),
        updatedAt: DateTime.utc_now() |> DateTime.add(-:rand.uniform(24) * 3600) |> DateTime.to_iso8601(),
        completedAt: if(status == "completed", do: DateTime.utc_now() |> DateTime.add(-:rand.uniform(12) * 3600) |> DateTime.to_iso8601(), else: nil),
        notes: []
      }
    end
  end
end
