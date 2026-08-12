<!DOCTYPE html>
<html lang="en" class="h-full bg-[#C87F37]">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2DA — Registration Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    
    <style>
        body { font-family: 'Plus Jakarta Sans', sans-serif; }
        .glass-card {
            background: #E3BC90;
            border: 1px solid #c99c6b;
            box-shadow: 0 25px 50px -12px rgba(100, 50, 0, 0.4);
        }
        .input-field {
            background-color: #F5E6D3;
            border-color: #d4aa7c;
            color: #0f172a; 
        }
        .input-field:focus {
            border-color: #78350f; /* amber-900 */
        }
        .input-field::placeholder {
            color: #92400e; 
            opacity: 0.6;
        }
    </style>
</head>
<body class="min-h-full text-slate-900 antialiased flex flex-col justify-center items-center py-10 px-4 relative bg-[#C87F37]">

    <div class="w-full max-w-xl glass-card rounded-3xl p-6 sm:p-8 relative z-10">
        
        <!-- Header -->
        <div class="text-center mb-8">
            <div class="inline-flex items-center justify-center w-14 h-14 bg-amber-900 rounded-2xl mb-3 shadow-lg shadow-amber-900/30 border border-amber-950/20">
                <i class="fa-solid fa-motorcycle text-2xl text-white"></i>
            </div>
            <h1 class="text-3xl font-extrabold tracking-tight text-slate-900">
                2DA Registration
            </h1>
            <p class="text-xs font-extrabold uppercase tracking-widest text-amber-900 mt-1">Hyper-Local Community Platform</p>
        </div>

        <!-- Role Switcher -->
        <div class="grid grid-cols-2 p-1.5 bg-[#e8cda8] rounded-2xl border border-[#d4aa7c] mb-6 shadow-inner">
            <button id="btn-passenger" onclick="switchRole('passenger')" type="button" class="py-3 text-sm font-bold rounded-xl transition-all duration-300 bg-amber-900 text-white shadow-md shadow-amber-900/30">
                <i class="fa-solid fa-user mr-2"></i>Passenger
            </button>
            <button id="btn-driver" onclick="switchRole('driver')" type="button" class="py-3 text-sm font-bold rounded-xl text-amber-900 hover:text-amber-950 transition-all duration-300">
                <i class="fa-solid fa-id-card mr-2"></i>Tricycle Driver
            </button>
        </div>

        <!-- Alert Box for Password Mismatch -->
        <div id="alert-box" class="hidden mb-6 p-4 rounded-xl text-sm font-bold border border-red-800/30 bg-red-100 text-red-800"></div>

        <!-- ==================== PASSENGER REGISTRATION FORM ==================== -->
        <form id="form-passenger" action="/register-account/" method="POST" enctype="multipart/form-data" class="space-y-4" onsubmit="return validatePasswords('passenger')">
            <input type="hidden" name="role" value="passenger">

            <div>
                <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">Full Name *</label>
                <input type="text" name="full_name" required placeholder="e.g., Juan Dela Cruz" 
                       class="input-field w-full border rounded-xl px-4 py-3.5 text-sm outline-none transition-all font-medium">
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                    <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">Create Username *</label>
                    <input type="text" name="username" required placeholder="Choose a username" 
                           class="input-field w-full border rounded-xl px-4 py-3.5 text-sm outline-none transition-all font-medium">
                </div>
                <div>
                    <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">Mobile / WhatsApp No. *</label>
                    <input type="text" name="whatsapp_number" required placeholder="09171234567" 
                           class="input-field w-full border rounded-xl px-4 py-3.5 text-sm outline-none transition-all font-medium">
                </div>
            </div>

            <!-- PASSWORD FIELDS -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                    <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">Password *</label>
                    <input type="password" name="password" id="pass-passenger" required placeholder="••••••••" 
                           class="input-field w-full border rounded-xl px-4 py-3.5 text-sm outline-none transition-all font-medium">
                </div>
                <div>
                    <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">Confirm Password *</label>
                    <input type="password" id="confirm-passenger" required placeholder="••••••••" 
                           class="input-field w-full border rounded-xl px-4 py-3.5 text-sm outline-none transition-all font-medium">
                </div>
            </div>

            <div>
                <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">Home Barangay / Community *</label>
                <input type="text" name="address" required placeholder="e.g., Brgy. San Antonio, Pasig City" 
                       class="input-field w-full border rounded-xl px-4 py-3.5 text-sm outline-none transition-all font-medium">
            </div>

            <button type="submit" class="w-full py-4 mt-2 bg-amber-900 hover:bg-amber-800 text-white font-bold rounded-xl shadow-lg shadow-amber-900/30 transition-all">
                Register Passenger Account <i class="fa-solid fa-arrow-right ml-2"></i>
            </button>
        </form>

        <!-- ==================== DRIVER REGISTRATION FORM ==================== -->
        <form id="form-driver" action="/register-account/" method="POST" enctype="multipart/form-data" class="space-y-4 hidden" onsubmit="return validatePasswords('driver')">
            <input type="hidden" name="role" value="driver">

            <div>
                <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">Full Name (On License) *</label>
                <input type="text" name="full_name" required placeholder="e.g., Pedro Penduko" 
                       class="input-field w-full border rounded-xl px-4 py-3.5 text-sm outline-none transition-all font-medium focus:border-green-800">
            </div>

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                    <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">Create Username *</label>
                    <input type="text" name="username" required placeholder="Choose a username" 
                           class="input-field w-full border rounded-xl px-4 py-3.5 text-sm outline-none transition-all font-medium focus:border-green-800">
                </div>
                <div>
                    <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">Mobile / WhatsApp No. *</label>
                    <input type="text" name="whatsapp_number" id="driver-mobile" required placeholder="09181234567" 
                           class="input-field w-full border rounded-xl px-4 py-3.5 text-sm outline-none transition-all font-medium focus:border-green-800">
                </div>
            </div>

            <!-- PASSWORD FIELDS -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                    <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">Password *</label>
                    <input type="password" name="password" id="pass-driver" required placeholder="••••••••" 
                           class="input-field w-full border rounded-xl px-4 py-3.5 text-sm outline-none transition-all font-medium focus:border-green-800">
                </div>
                <div>
                    <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">Confirm Password *</label>
                    <input type="password" id="confirm-driver" required placeholder="••••••••" 
                           class="input-field w-full border rounded-xl px-4 py-3.5 text-sm outline-none transition-all font-medium focus:border-green-800">
                </div>
            </div>

            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">Driver's License No. *</label>
                    <input type="text" name="toda_number" required placeholder="A01-23-456789" 
                           class="input-field w-full border rounded-xl px-4 py-3.5 text-sm outline-none transition-all font-medium focus:border-green-800">
                </div>
                <div>
                    <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">2DA Body / Plate No. *</label>
                    <input type="text" name="address" required placeholder="042 / 123-ABC" 
                           class="input-field w-full border rounded-xl px-4 py-3.5 text-sm outline-none transition-all font-medium focus:border-green-800">
                </div>
            </div>

            <!-- PAYOUT SELECTION -->
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                    <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">Payout Provider *</label>
                    <div class="relative">
                        <select name="bank_name" required class="input-field w-full border rounded-xl px-4 py-3.5 text-sm outline-none transition-all font-medium focus:border-green-800 appearance-none cursor-pointer">
                            <option value="GCash" selected>📱 GCash</option>
                            <option value="Maya">💳 Maya</option>
                            <option value="BPI">🏦 BPI</option>
                            <option value="BDO">🏦 BDO</option>
                            <option value="Landbank">🏦 Landbank</option>
                            <option value="UnionBank">🏦 UnionBank</option>
                            <option value="Metrobank">🏦 Metrobank</option>
                            <option value="RCBC">🏦 RCBC</option>
                            <option value="Other Bank">🏛️ Other Bank</option>
                        </select>
                        <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-amber-900">
                            <i class="fa-solid fa-chevron-down text-xs"></i>
                        </div>
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-1">Account Number *</label>
                    <p class="text-[10px] text-green-700 font-extrabold mb-1.5"><i class="fa-solid fa-lightbulb"></i> Can be your Wife's GCash/Maya number!</p>
                    <input type="text" name="gcash_account" id="driver-acct" required placeholder="e.g., 09171234567" 
                           pattern="[0-9]{11}" maxlength="11" title="Must be exactly 11 numbers (e.g. 09171234567)"
                           oninput="this.value = this.value.replace(/[^0-9]/g, '')"
                           class="input-field w-full border rounded-xl px-4 py-3.5 text-sm outline-none transition-all font-medium focus:border-green-800">
                </div>
            </div>

            <div>
                <label class="block text-xs font-bold text-amber-900 uppercase tracking-wider mb-2">Upload TODA ID / License Photo</label>
                <input type="file" name="toda_id" class="w-full text-xs text-slate-700 font-medium file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-green-800 file:text-white hover:file:bg-green-700 transition">
            </div>

            <button type="submit" class="w-full py-4 mt-2 bg-green-800 hover:bg-green-700 text-white font-bold rounded-xl shadow-lg shadow-green-900/30 transition-all">
                Submit Driver Credentials <i class="fa-solid fa-shield-check ml-2"></i>
            </button>
        </form>

        <!-- Footer Link -->
        <div class="text-center mt-6 pt-4 border-t border-[#c99c6b]">
            <p class="text-xs font-bold text-slate-700">Already have an account? <a href="login.html" class="text-amber-900 hover:text-amber-800 underline transition">Log in here</a></p>
        </div>

    </div>

    <script>
        // Switches the visible form between Passenger and Driver
        function switchRole(role) {
            const btnPassenger = document.getElementById('btn-passenger');
            const btnDriver = document.getElementById('btn-driver');
            const formPassenger = document.getElementById('form-passenger');
            const formDriver = document.getElementById('form-driver');
            const alertBox = document.getElementById('alert-box');

            alertBox.classList.add('hidden'); // Hide alerts on switch

            if (role === 'passenger') {
                btnPassenger.className = "py-3 text-sm font-bold rounded-xl transition-all duration-300 bg-amber-900 text-white shadow-md shadow-amber-900/30";
                btnDriver.className = "py-3 text-sm font-bold rounded-xl text-amber-900 hover:text-amber-950 transition-all duration-300";
                formPassenger.classList.remove('hidden');
                formDriver.classList.add('hidden');
            } else {
                btnDriver.className = "py-3 text-sm font-bold rounded-xl transition-all duration-300 bg-green-800 text-white shadow-md shadow-green-900/30";
                btnPassenger.className = "py-3 text-sm font-bold rounded-xl text-amber-900 hover:text-amber-950 transition-all duration-300";
                formDriver.classList.remove('hidden');
                formPassenger.classList.add('hidden');
            }
        }

        // Checks if Password and Confirm Password match before submitting to backend
        function validatePasswords(role) {
            const pass = document.getElementById(`pass-${role}`).value;
            const confirm = document.getElementById(`confirm-${role}`).value;
            const alertBox = document.getElementById('alert-box');

            if (pass !== confirm) {
                alertBox.innerHTML = "⚠️ Passwords do not match! Please verify and try again.";
                alertBox.classList.remove('hidden');
                return false; // Prevents form submission
            }
            return true; // Allows form submission
        }
    </script>
</body>
</html>
