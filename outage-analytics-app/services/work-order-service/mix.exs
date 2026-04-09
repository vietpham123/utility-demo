defmodule WorkOrderService.MixProject do
  use Mix.Project

  def project do
    [
      app: :work_order_service,
      version: "1.0.0",
      elixir: "~> 1.16",
      start_permanent: Mix.env() == :prod,
      deps: deps(),
      releases: [
        work_order_service: [
          include_executables_for: [:unix]
        ]
      ]
    ]
  end

  def application do
    [
      extra_applications: [:logger],
      mod: {WorkOrderService.Application, []}
    ]
  end

  defp deps do
    [
      {:plug_cowboy, "~> 2.7"},
      {:plug, "~> 1.15"},
      {:jason, "~> 1.4"},
      {:httpoison, "~> 2.2"}
    ]
  end
end
