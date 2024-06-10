

using Microsoft.AspNetCore.Mvc; // �ޤJ ASP.NET Core MVC �R�W�Ŷ�
using System.Diagnostics; // �ޤJ�E�_�R�W�Ŷ��A�Ω����~���i�{
using Technical_Indicators_System.Models; // �ޤJ�ҫ��R�W�Ŷ�

namespace Technical_Indicators_System.Controllers // �R�W�Ŷ��w�q
{
    public class HomeController : Controller // ������A�~�Ӧ� Controller
    {
        private readonly ILogger<HomeController> _logger; // �w�q�uŪ����x�O����

        public HomeController(ILogger<HomeController> logger) // ����c�y��ơA������x�O�����Ѽ�
        {
            _logger = logger; // ��l�Ƥ�x�O����
        }

        public IActionResult Index() // �B�z Index �ШD
        {
            return View(); // ��^ Index ����
        }

        public IActionResult Privacy() // �B�z Privacy �ШD
        {
            return View(); // ��^ Privacy ����
        }

        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)] // �T���T���w�s
        public IActionResult Error() // �B�z Error �ШD
        {
            return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier }); // ��^ Error ���ϡA�öǻ� ErrorViewModel
        }

        public IActionResult MACD() // �B�z MACD �ШD
        {
            return View(); // ��^ MACD ����
        }

        [HttpPost] // ���w����k�B�z POST �ШD
        public IActionResult ProcessMACDInputs(int ma1, int ma2, string stdate, string eddate, string ticker, int slicer)
        {
            // �ե� ExecutePythonScript ��k���� Python �}���A�ñN���G���w�V�� MACDResult ��k
            return ExecutePythonScript("MACD_Oscillator_backtest.py", new object[] { ma1, ma2, stdate, eddate, ticker, slicer }, "MACDResult");
        }

        public IActionResult MACDResult() // �B�z MACDResult �ШD
        {
            // �ե� GenerateResultView ��k�ͦ����G����
            return GenerateResultView("MACDResult", "output_positions_MACD.png", "output_macd.png");
        }

        public IActionResult Pair() // �B�z Pair �ШD
        {
            _logger.LogInformation("Pair action called."); // �O����x�H��
            return View(); // ��^ Pair ����
        }

        [HttpPost] // ���w����k�B�z POST �ШD
        public IActionResult ProcessPairInputs(string stdate, string eddate, string ticker1, string ticker2)
        {
            // �O����J�Ѽƪ��H��
            _logger.LogInformation($"ProcessPairInputs called with stdate: {stdate}, eddate: {eddate}, ticker1: {ticker1}, ticker2: {ticker2}");
            // �ե� ExecutePythonScript ��k���� Python �}���A�ñN���G���w�V�� PairResult ��k
            return ExecutePythonScript("Pair_trading_backtest.py", new object[] { stdate, eddate, ticker1, ticker2 }, "PairResult");
        }

        public IActionResult PairResult() // �B�z PairResult �ШD
        {
            _logger.LogInformation("PairResult action called."); // �O����x�H��
            // �ե� GenerateResultView ��k�ͦ����G����
            return GenerateResultView("PairResult", "output_positions_Pair.png", "output_Pair_portfolio.png");
        }

        public IActionResult Heikin_Ashi() // �B�z Heikin_Ashi �ШD
        {
            _logger.LogInformation("Heikin_Ashi action called."); // �O����x�H��
            return View(); // ��^ Heikin_Ashi ����
        }

        [HttpPost] // ���w����k�B�z POST �ШD
        public IActionResult ProcessHeikin_AshiInputs(string ticker, string stdate, string eddate)
        {
            // �O����J�Ѽƪ��H��
            _logger.LogInformation($"ProcessHeikin_AshiInputs called with stdate: {stdate}, eddate: {eddate}, ticker: {ticker}");
            // �ե� ExecutePythonScript ��k���� Python �}���A�ñN���G���w�V�� Heikin_AshiResult ��k
            return ExecutePythonScript("Heikin_Ashi_backtest.py", new object[] { ticker, stdate, eddate }, "Heikin_AshiResult");
        }

        public IActionResult Heikin_AshiResult() // �B�z Heikin_AshiResult �ШD
        {
            _logger.LogInformation("Heikin_AshiResult action called."); // �O����x�H��
            // �ե� GenerateResultView ��k�ͦ����G����
            return GenerateResultView("Heikin_AshiResult", "output_positions_HeikinAshi.png", "output_HeikinAshi_portfolio.png");
        }

        private IActionResult ExecutePythonScript(string scriptName, object[] args, string resultAction)
        {
            try
            {
                // �]�m Python �}���M�����ɸ��|
                string pythonScriptPath = Path.Combine(Directory.GetCurrentDirectory(), "PythonScripts", "quant-trading-master", scriptName);
                string pythonExePath = @"C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python39_64\python.exe"; // �קאּ�z��python.exe���|
                string outputDir = Path.Combine(Directory.GetCurrentDirectory(), "wwwroot", "images");

                // �]�m ProcessStartInfo �H���� Python �}��
                var start = new ProcessStartInfo
                {
                    FileName = pythonExePath,
                    Arguments = $"{pythonScriptPath} {string.Join(" ", args)} {outputDir}",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true
                };

                string result, error;
                using (var process = Process.Start(start)) // �}�l�i�{
                {
                    using (var reader = process.StandardOutput) // Ū���зǿ�X
                    {
                        result = reader.ReadToEnd();
                    }
                    using (var reader = process.StandardError) // Ū���зǿ��~
                    {
                        error = reader.ReadToEnd();
                    }
                }

                TempData["PythonOutput"] = result; // �N Python ��X�s�x�� TempData
                TempData["PythonError"] = error; // �N Python ���~�H���s�x�� TempData
                for (int i = 0; i < args.Length; i++)
                {
                    TempData[$"Arg{i}"] = args[i].ToString(); // �N��J�ѼƦs�x�� TempData
                }

                return RedirectToAction(resultAction); // ���w�V�쵲�G�ʧ@
            }
            catch (Exception ex)
            {
                TempData["PythonError"] = ex.Message; // �N���`�H���s�x�� TempData
                return RedirectToAction(resultAction); // ���w�V�쵲�G�ʧ@
            }
        }

        private IActionResult GenerateResultView(string viewName, string positionsFileName, string macdFileName)
        {
            ViewBag.PythonOutput = TempData["PythonOutput"]; // �q TempData ����� Python ��X�æs�x�� ViewBag
            ViewBag.PythonError = TempData["PythonError"]; // �q TempData ����� Python ���~�H���æs�x�� ViewBag

            for (int i = 0; TempData.ContainsKey($"Arg{i}"); i++) // �q TempData �������J�Ѽƨæs�x�� ViewData
            {
                ViewData[$"Arg{i}"] = TempData[$"Arg{i}"];
            }

            // �]�m�Ϥ������|
            ViewBag.PositionsPath = Path.Combine("/images", positionsFileName);
            ViewBag.MacdPath = Path.Combine("/images", macdFileName);

            return View(viewName); // ��^���w�����ϦW��
        }
    }
}
