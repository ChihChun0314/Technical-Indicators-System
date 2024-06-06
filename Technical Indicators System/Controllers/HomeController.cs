using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;
using Technical_Indicators_System.Models;

namespace Technical_Indicators_System.Controllers
{
    public class HomeController : Controller
    {
        private readonly ILogger<HomeController> _logger;

        public HomeController(ILogger<HomeController> logger)
        {
            _logger = logger;
        }

        public IActionResult Index()
        {
            return View();
        }

        public IActionResult Privacy()
        {
            return View();
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
        }

        public IActionResult MACD()
        {
            return View();
        }
        [HttpPost]
        public IActionResult ProcessMACDInputs(int ma1, int ma2, string stdate, string eddate, string ticker, int slicer)
        {
            // �N��J�ȶǻ��� ViewBag
            ViewBag.Ma1 = ma1;
            ViewBag.Ma2 = ma2;
            ViewBag.Stdate = stdate;
            ViewBag.Eddate = eddate;
            ViewBag.Ticker = ticker;
            ViewBag.Slicer = slicer;

            // �]�m Python �}���M�����ɸ��|
            string pythonScriptPath = @"C:\Users\Jason\Desktop\Technical Indicators System\Technical Indicators System\PythonScripts\quant-trading-master\MACD Oscillator backtest.py";
            string pythonExePath = @"C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python39_64\python.exe";

            // �]�m ProcessStartInfo �H���� Python �}��
            ProcessStartInfo start = new ProcessStartInfo();
            start.FileName = pythonExePath;
            start.Arguments = $"{pythonScriptPath} {ma1} {ma2} {stdate} {eddate} {ticker} {slicer}"; // �N��J�Ѽƶǻ��� Python �}��
            start.UseShellExecute = false;
            start.RedirectStandardOutput = true;
            start.RedirectStandardError = true;

            string result = "";
            using (Process process = Process.Start(start))
            {
                using (StreamReader reader = process.StandardOutput)
                {
                    result = reader.ReadToEnd();
                }
            }

            // �N Python �}������X�s�x�� TempData �H�K�b���w�V��ϥ�
            TempData["PythonOutput"] = result;
            TempData["Ma1"] = ma1;
            TempData["Ma2"] = ma2;
            TempData["Stdate"] = stdate;
            TempData["Eddate"] = eddate;
            TempData["Ticker"] = ticker;
            TempData["Slicer"] = slicer;

            // ��^ MACD ���ϡA�ϥ� TempData �ǻ��ƾ�
            return RedirectToAction("MACDResult");
        }
        public IActionResult MACDResult()
        {
            // �N TempData �����ƾڦs�x�� ViewBag
            ViewBag.PythonOutput = TempData["PythonOutput"];
            ViewBag.Ma1 = TempData["Ma1"];
            ViewBag.Ma2 = TempData["Ma2"];
            ViewBag.Stdate = TempData["Stdate"];
            ViewBag.Eddate = TempData["Eddate"];
            ViewBag.Ticker = TempData["Ticker"];
            ViewBag.Slicer = TempData["Slicer"];

            // ����Ϥ����|
            string positionsPath = Path.Combine("~/images", "output_positions.png");
            string macdPath = Path.Combine("~/images", "output_macd.png");
            ViewBag.PositionsPath = positionsPath;
            ViewBag.MacdPath = macdPath;

            return View();
        }
    }
}
