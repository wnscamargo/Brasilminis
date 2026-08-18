@if (session('success') || session('error') || $errors->any())
<div x-data="{ show: true }" x-show="show" x-init="setTimeout(() => show = false, 5000)"
     class="fixed top-24 right-4 z-[200] max-w-sm space-y-2">
    @if (session('success'))
        <div class="bm-card bg-bm-green/15 border-bm-green/40 text-green-300 px-5 py-3 text-sm" data-testid="flash-success">
            {{ session('success') }}
        </div>
    @endif
    @if (session('error'))
        <div class="bm-card bg-red-500/15 border-red-500/40 text-red-300 px-5 py-3 text-sm" data-testid="flash-error">
            {{ session('error') }}
        </div>
    @endif
    @if ($errors->any())
        <div class="bm-card bg-red-500/15 border-red-500/40 text-red-300 px-5 py-3 text-sm">
            {{ $errors->first() }}
        </div>
    @endif
</div>
@endif
