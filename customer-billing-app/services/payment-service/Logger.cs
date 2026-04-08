using Microsoft.Extensions.Logging;

namespace PaymentService
{
    public static class LoggerFactory
    {
        private static ILoggerFactory _factory;
        public static ILogger CreateLogger<T>()
        {
            if (_factory == null)
            {
                _factory = Microsoft.Extensions.Logging.LoggerFactory.Create(builder =>
                {
                    builder.AddConsole();
                });
            }
            return _factory.CreateLogger<T>();
        }
    }
}
