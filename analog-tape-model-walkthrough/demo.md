# AnalogTapeModel DSP Walkthrough

*2026-03-09T00:17:16Z by Showboat 0.6.1*
<!-- showboat-id: d3f98c20-0c4b-4fc9-89c1-289a5c38ae79 -->

This walkthrough follows the **audio-processing path only** in `jatinchowdhury18/AnalogTapeModel`, pinned to commit `604372e4ffd9690c3e283362e4598cb43edbb475` so the code references stay stable.

The target reader already understands audio engineering and Python-style programming, but not C++. The main translation trick is:

- `prepareToPlay(...)` = one-time setup, like initializing state before streaming
- `processAudioBlock(AudioBuffer<float>& buffer)` = the per-buffer callback, like processing one NumPy array chunk in place
- `processor.processBlock(buffer)` = “run this DSP stage on the current audio block”
- `AudioBuffer<float>&` = a mutable audio block passed by reference, so each stage edits the same buffer in place

We'll start from the top-level plugin callback, then drill into each DSP subsystem in the same order the signal sees them.

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py stage-order
```

```cpp
AnalogTapeModel commit: 604372e4ffd9690c3e283362e4598cb43edbb475
Signal path inside processAudioBlock():
 1. L169: dryBuffer.makeCopyOf (buffer, true);
    Copy the untouched input into a parallel dry path for later dry/wet mixing.
 2. L170: inGain.processBlock (buffer);
    Apply the user-controlled input gain before the tape model.
 3. L171: inputFilters.processBlock (buffer);
    Apply optional input high-pass / low-pass filtering and capture the removed bands for optional makeup.
 4. L173: scope->pushSamplesIO (buffer, TapeScope::AudioType::Input);
    Send the pre-tape signal to the visualizer.
 5. L175: midSideController.processInput (buffer);
    Optionally convert stereo to mid/side and apply stereo balance before the nonlinear stages.
 6. L176: toneControl.processBlockIn (buffer);
    Apply the pre-emphasis tone stage before the tape core.
 7. L177: compressionProcessor.processBlock (buffer);
    Apply input compression with oversampled gain reduction.
 8. L178: hysteresis.processBlock (buffer);
    Run the core tape hysteresis model that generates saturation, bias-related behavior, and memory effects.
 9. L179: toneControl.processBlockOut (buffer);
    Apply the complementary de-emphasis tone stage after hysteresis.
10. L180: chewer.processBlock (buffer);
    Add intermittent tape-chew/dropout style damage.
11. L181: degrade.processBlock (buffer);
    Add noise, bandwidth loss, and level-dependent degradation.
12. L182: flutter.processBlock (buffer);
    Apply wow and flutter as a time-varying delay modulation.
13. L183: lossFilter.processBlock (buffer);
    Apply playback-head loss filters and azimuth mismatch.
14. L185: latencyCompensation();
    Delay the dry path and filter-makeup path so they stay phase-aligned with the wet path.
15. L187: midSideController.processOutput (buffer);
    Decode back from mid/side and undo stereo balance makeup if enabled.
16. L188: inputFilters.processBlockMakeup (buffer);
    Optionally add the removed low/high bands back into the post-latency-compensated signal.
17. L189: outGain.processBlock (buffer);
    Apply output gain.
18. L190: dryWet.processBlock (dryBuffer, buffer);
    Blend the delayed dry path with the processed wet path.
19. L192: chowdsp::BufferMath::sanitizeBuffer (buffer);
    Clean up NaNs/denormals before output.
20. L194: scope->pushSamplesIO (buffer, TapeScope::AudioType::Output);
    Send the final post-tape signal to the visualizer.
```

That stage list is the backbone of the walkthrough. The plugin keeps a **parallel dry copy** from the start, pushes the wet path through several tape-inspired processors, then re-aligns the dry path for a final blend.

Before any audio runs, `prepareToPlay()` wires up sample rates, oversampling, buffers, and latency compensation. Notice that latency is not treated as a generic host-side problem only; the code also delays its own dry path and its filter-makeup path so the blend stays phase-coherent.

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/PluginProcessor.cpp 'void ChowtapeModelAudioProcessor::prepareToPlay' 'void ChowtapeModelAudioProcessor::releaseResources'
```

```cpp
Plugin/Source/PluginProcessor.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
  93: void ChowtapeModelAudioProcessor::prepareToPlay (double sampleRate, int samplesPerBlock)
  94: {
  95:     const auto numChannels = getTotalNumInputChannels();
  96:     setRateAndBufferSizeDetails (sampleRate, samplesPerBlock);
  97: 
  98:     inGain.prepareToPlay (sampleRate, samplesPerBlock);
  99:     inputFilters.prepareToPlay (sampleRate, samplesPerBlock, numChannels);
 100:     midSideController.prepare (sampleRate, samplesPerBlock);
 101:     toneControl.prepare (sampleRate, numChannels);
 102:     compressionProcessor.prepare (sampleRate, samplesPerBlock, numChannels);
 103:     hysteresis.prepareToPlay (sampleRate, samplesPerBlock, numChannels);
 104:     degrade.prepareToPlay (sampleRate, samplesPerBlock, numChannels);
 105:     chewer.prepare (sampleRate, samplesPerBlock, numChannels);
 106:     lossFilter.prepare ((float) sampleRate, samplesPerBlock, numChannels);
 107: 
 108:     dryDelay.prepare ({ sampleRate, (uint32) samplesPerBlock, (uint32) numChannels });
 109:     dryDelay.setDelay (calcLatencySamples());
 110: 
 111:     flutter.prepareToPlay (sampleRate, samplesPerBlock, numChannels);
 112:     outGain.prepareToPlay (sampleRate, samplesPerBlock);
 113: 
 114:     scope->setNumChannels (numChannels);
 115:     scope->prepareToPlay (sampleRate, samplesPerBlock);
 116: 
 117:     dryWet.setDryWet (*vts.getRawParameterValue ("drywet") / 100.0f);
 118:     dryWet.reset();
 119:     dryBuffer.setSize (numChannels, samplesPerBlock);
 120: 
 121:     setLatencySamples (roundToInt (calcLatencySamples()));
 122:     magicState.getPropertyAsValue (isStereoTag).setValue (numChannels == 2);
 123: }
 124: 
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/PluginProcessor.cpp 'float ChowtapeModelAudioProcessor::calcLatencySamples' 'bool ChowtapeModelAudioProcessor::isBusesLayoutSupported'
```

```cpp
Plugin/Source/PluginProcessor.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
 130: float ChowtapeModelAudioProcessor::calcLatencySamples() const noexcept
 131: {
 132:     return lossFilter.getLatencySamples() + hysteresis.getLatencySamples() + compressionProcessor.getLatencySamples();
 133: }
 134: 
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/PluginProcessor.cpp 'void ChowtapeModelAudioProcessor::latencyCompensation' 'AudioProcessorEditor* ChowtapeModelAudioProcessor::createEditor'
```

```cpp
Plugin/Source/PluginProcessor.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
 197: void ChowtapeModelAudioProcessor::latencyCompensation()
 198: {
 199:     // delay dry buffer to avoid phase issues
 200:     const auto latencySampFloat = calcLatencySamples();
 201:     const auto latencySamp = roundToInt (latencySampFloat);
 202:     setLatencySamples (latencySamp);
 203: 
 204:     // delay makeup block from input filters
 205:     inputFilters.setMakeupDelay (latencySampFloat);
 206: 
 207:     // For "true bypass" use integer sample delay to avoid delay
 208:     // line interpolation freq. response issues
 209:     if (dryWet.getDryWet() < 0.15f)
 210:     {
 211:         dryDelay.setDelay ((float) latencySamp);
 212:     }
 213:     else
 214:     {
 215:         dryDelay.setDelay (latencySampFloat);
 216:     }
 217: 
 218:     dsp::AudioBlock<float> block { dryBuffer };
 219:     dryDelay.process (dsp::ProcessContextReplacing<float> { block });
 220: }
 221: 
```

## 1. Input conditioning: gain, filters, stereo domain, and tone pre-shaping

The first group of stages prepares the signal before the main tape nonlinearity:

1. **Input gain** sets the drive level into the model.
2. **Input filters** can remove low or high bands before saturation.
3. **Mid/side + stereo balance** optionally changes the stereo domain and channel emphasis.
4. **ToneControl input stage** applies a pre-emphasis style tilt before hysteresis.

A key detail: the input filters store the removed low/high components into side buffers, then optionally add them back *later* after latency alignment. That lets the user filter what hits the nonlinear core without permanently deleting those bands from the final output.

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Input_Filters/InputFilters.cpp 'void InputFilters::processBlock' 'void InputFilters::processBlockMakeup'
```

```cpp
Plugin/Source/Processors/Input_Filters/InputFilters.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
  69: void InputFilters::processBlock (AudioBuffer<float>& buffer)
  70: {
  71:     if (! bypass.processBlockIn (buffer, bypass.toBool (onOffParam)))
  72:         return;
  73: 
  74:     lowCutFilter.setCutoff (lowCutParam->getCurrentValue());
  75:     highCutFilter.setCutoff (jmin (highCutParam->getCurrentValue(), fs * 0.48f));
  76: 
  77:     for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
  78:     {
  79:         auto* data = buffer.getWritePointer (ch);
  80:         auto* cutLowSignal = lowCutBuffer.getWritePointer (ch);
  81:         auto* cutHighSignal = highCutBuffer.getWritePointer (ch);
  82: 
  83:         for (int n = 0; n < buffer.getNumSamples(); ++n)
  84:         {
  85:             lowCutFilter.processSample ((size_t) ch, data[n], cutLowSignal[n], data[n]);
  86:             highCutFilter.processSample ((size_t) ch, data[n], data[n], cutHighSignal[n]);
  87:         }
  88:     }
  89: 
  90:     bypass.processBlockOut (buffer, bypass.toBool (onOffParam));
  91: 
  92:     lowCutFilter.snapToZero();
  93:     highCutFilter.snapToZero();
  94: }
  95: 
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Input_Filters/InputFilters.cpp 'void InputFilters::processBlockMakeup' '__EOF__'
```

```cpp
Plugin/Source/Processors/Input_Filters/InputFilters.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
  96: void InputFilters::processBlockMakeup (AudioBuffer<float>& buffer)
  97: {
  98:     if (! makeupBypass.processBlockIn (buffer, bypass.toBool (onOffParam)))
  99:         return;
 100: 
 101:     if (! static_cast<bool> (makeupParam->load()))
 102:     {
 103:         makeupBypass.processBlockOut (buffer, bypass.toBool (onOffParam));
 104:         return;
 105:     }
 106: 
 107:     // compile makeup signal
 108:     makeupBuffer.setSize (buffer.getNumChannels(), buffer.getNumSamples(), false, false, true);
 109:     dsp::AudioBlock<float> lowCutBlock (lowCutBuffer);
 110:     dsp::AudioBlock<float> highCutBlock (highCutBuffer);
 111:     dsp::AudioBlock<float> makeupBlock (makeupBuffer);
 112: 
 113:     makeupBlock.fill (0.0f);
 114:     makeupBlock += lowCutBlock;
 115:     makeupBlock += highCutBlock;
 116: 
 117:     // delay makeup signal to be in phase with everything else
 118:     dsp::ProcessContextReplacing<float> context (makeupBlock);
 119:     makeupDelay.process (context);
 120: 
 121:     // add makeup back to main buffer
 122:     dsp::AudioBlock<float> outputBlock (buffer);
 123:     outputBlock += makeupBlock;
 124: 
 125:     makeupBypass.processBlockOut (buffer, bypass.toBool (onOffParam));
 126: }
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/MidSide/MidSideProcessor.cpp 'void MidSideProcessor::processInput' 'void MidSideProcessor::processOutput'
```

```cpp
Plugin/Source/Processors/MidSide/MidSideProcessor.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
  44: void MidSideProcessor::processInput (AudioBuffer<float>& buffer)
  45: {
  46:     if (buffer.getNumChannels() != 2) // needs to be stereo!
  47:         return;
  48: 
  49:     //mid - side encoding logic here
  50:     const auto numSamples = buffer.getNumSamples();
  51:     if (curMS)
  52:     {
  53:         buffer.addFrom (0, 0, buffer, 1, 0, numSamples); // make channel 0 = left + right = mid
  54:         buffer.applyGain (1, 0, numSamples, 2.0f); // make channel 1 = 2 * right
  55:         buffer.addFrom (1, 0, buffer, 0, 0, numSamples, -1.0f); // make channel 1 = (2 * right) - (left + right) = right - left
  56:         buffer.applyGain (1, 0, numSamples, -1.0f); // make channel 1 = -1 * (right - left) = left - right = side
  57: 
  58:         buffer.applyGain (Decibels::decibelsToGain (-3.0f)); // -3 dB Normalization
  59:     }
  60: 
  61:     // balance processing
  62:     const auto curBalance = balanceParam->getCurrentValue();
  63:     auto&& stereoBlock = dsp::AudioBlock<float> { buffer };
  64:     auto&& leftBlock = stereoBlock.getSingleChannelBlock (0);
  65:     auto&& rightBlock = stereoBlock.getSingleChannelBlock (1);
  66: 
  67:     inBalanceGain[0].setGainDecibels (curBalance * balanceGainDB);
  68:     inBalanceGain[0].process (dsp::ProcessContextReplacing<float> { leftBlock });
  69: 
  70:     inBalanceGain[1].setGainDecibels (curBalance * -balanceGainDB);
  71:     inBalanceGain[1].process (dsp::ProcessContextReplacing<float> { rightBlock });
  72: }
  73: 
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/MidSide/MidSideProcessor.cpp 'void MidSideProcessor::processOutput' '__EOF__'
```

```cpp
Plugin/Source/Processors/MidSide/MidSideProcessor.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
  74: void MidSideProcessor::processOutput (AudioBuffer<float>& buffer)
  75: {
  76:     if (buffer.getNumChannels() != 2) // needs to be stereo!
  77:         return;
  78: 
  79:     if (prevMS != (*midSideParam == 1.0f) && ! fadeSmooth.isSmoothing())
  80:     {
  81:         fadeSmooth.setCurrentAndTargetValue (1.0f);
  82:         fadeSmooth.setTargetValue (0.0f);
  83:     }
  84: 
  85:     // inverse balance processing
  86:     if (*makeupParam == 1.0f)
  87:     {
  88:         const auto curBalance = balanceParam->getCurrentValue();
  89:         auto&& stereoBlock = dsp::AudioBlock<float> { buffer };
  90:         auto&& leftBlock = stereoBlock.getSingleChannelBlock (0);
  91:         auto&& rightBlock = stereoBlock.getSingleChannelBlock (1);
  92: 
  93:         outBalanceGain[0].setGainDecibels (curBalance * -balanceGainDB);
  94:         outBalanceGain[0].process (dsp::ProcessContextReplacing<float> { leftBlock });
  95: 
  96:         outBalanceGain[1].setGainDecibels (curBalance * balanceGainDB);
  97:         outBalanceGain[1].process (dsp::ProcessContextReplacing<float> { rightBlock });
  98:     }
  99: 
 100:     //mid - side decoding logic here
 101:     const auto numSamples = buffer.getNumSamples();
 102:     if (curMS)
 103:     {
 104:         buffer.applyGain (Decibels::decibelsToGain (3.0f)); // undo -3 dB Normalization
 105: 
 106:         buffer.applyGain (1, 0, numSamples, -1.0f); // channel 1 = (L - R) * -1 = R - L
 107:         buffer.addFrom (0, 0, buffer, 1, 0, numSamples, -1.0f); // channel 0 = (L + R) - (R - L) = 2L
 108:         buffer.applyGain (0, 0, numSamples, 0.5f); // channel 0: 0.5 * (2L) = L
 109:         buffer.addFrom (1, 0, buffer, 0, 0, numSamples); // channel 1 = (R - L) + L = R
 110:     }
 111: 
 112:     if (fadeSmooth.isSmoothing())
 113:     {
 114:         float startGain = fadeSmooth.getCurrentValue();
 115:         float endGain = fadeSmooth.skip (numSamples);
 116: 
 117:         buffer.applyGainRamp (0, numSamples, startGain, endGain);
 118: 
 119:         if (endGain == 0.0f)
 120:         {
 121:             fadeSmooth.setTargetValue (1.0f);
 122: 
 123:             // reset curMS at the "bottom" of the fade
 124:             curMS = *midSideParam == 1.0f;
 125:             prevMS = curMS;
 126:         }
 127:     }
 128: }
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Hysteresis/ToneControl.cpp 'void ToneControl::processBlockIn' 'void ToneControl::processBlockOut'
```

```cpp
Plugin/Source/Processors/Hysteresis/ToneControl.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
 101: void ToneControl::processBlockIn (AudioBuffer<float>& buffer)
 102: {
 103:     if (static_cast<bool> (onOffParam->load()))
 104:     {
 105:         toneIn.setLowGain (dbScale * bassParam->getCurrentValue());
 106:         toneIn.setHighGain (dbScale * trebleParam->getCurrentValue());
 107:     }
 108:     else
 109:     {
 110:         toneIn.setLowGain (0.0f);
 111:         toneIn.setHighGain (0.0f);
 112:     }
 113:     toneIn.setTransFreq (tFreqParam->getCurrentValue());
 114: 
 115:     toneIn.processBlock (buffer);
 116: }
 117: 
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Hysteresis/ToneControl.cpp 'void ToneControl::processBlockOut' '__EOF__'
```

```cpp
Plugin/Source/Processors/Hysteresis/ToneControl.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
 118: void ToneControl::processBlockOut (AudioBuffer<float>& buffer)
 119: {
 120:     if (static_cast<bool> (onOffParam->load()))
 121:     {
 122:         toneOut.setLowGain (-1.0f * dbScale * bassParam->getCurrentValue());
 123:         toneOut.setHighGain (-1.0f * dbScale * trebleParam->getCurrentValue());
 124:     }
 125:     else
 126:     {
 127:         toneOut.setLowGain (0.0f);
 128:         toneOut.setHighGain (0.0f);
 129:     }
 130:     toneOut.setTransFreq (tFreqParam->getCurrentValue());
 131: 
 132:     toneOut.processBlock (buffer);
 133: }
```

## 2. Compression before hysteresis

`CompressionProcessor` lives *before* the tape core, so it shapes how hard the hysteresis model gets hit. The implementation oversamples internally, derives a transfer curve in dB, slew-limits the gain to get attack/release behavior, then downsamples back to the main stream.

This is not trying to imitate magnetic hysteresis itself. Instead, it is an extra front-end dynamic stage that changes the excitation of the later nonlinear model.

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Compression/CompressionProcessor.cpp 'void CompressionProcessor::processBlock' 'float CompressionProcessor::getLatencySamples'
```

```cpp
Plugin/Source/Processors/Compression/CompressionProcessor.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
  57: void CompressionProcessor::processBlock (AudioBuffer<float>& buffer)
  58: {
  59:     if (! bypass.processBlockIn (buffer, bypass.toBool (onOff)))
  60:         return;
  61: 
  62:     dsp::AudioBlock<float> block (buffer);
  63:     auto osBlock = oversample->processSamplesUp (block);
  64: 
  65:     const auto numSamples = (int) osBlock.getNumSamples();
  66:     for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
  67:     {
  68:         dbPlusSmooth[ch].setTargetValue (amountParam->getCurrentValue());
  69: 
  70:         auto* x = osBlock.getChannelPointer ((size_t) ch);
  71:         FloatVectorOperations::copy (xDBVec.data(), x, numSamples);
  72:         FloatVectorOperations::abs (xDBVec.data(), xDBVec.data(), numSamples);
  73: 
  74:         constexpr auto inc = xsimd::batch<float>::size;
  75:         size_t n = 0;
  76:         for (; n < (size_t) numSamples; n += inc)
  77:         {
  78:             auto xDB = xsimd::load_aligned (&xDBVec[n]);
  79: 
  80:             xDB = chowdsp::SIMDUtils::gainToDecibels (xDB);
  81:             auto compDB = compressionDB (xDB, dbPlusSmooth[ch].skip ((int) inc));
  82:             auto compGain = chowdsp::SIMDUtils::decibelsToGain (compDB);
  83: 
  84:             xsimd::store_aligned (&xDBVec[n], xDB);
  85:             xsimd::store_aligned (&compGainVec[n], compGain);
  86:         }
  87: 
  88:         // remaining samples that can't be vectorized
  89:         for (; n < (size_t) numSamples; ++n)
  90:         {
  91:             xDBVec[n] = Decibels::gainToDecibels (xDBVec[n]);
  92:             auto compDB = compressionDB (xDBVec[n], dbPlusSmooth[ch].getNextValue());
  93:             compGainVec[n] = Decibels::decibelsToGain (compDB);
  94:         }
  95: 
  96:         // since the slew will be applied to the gain, we need to reverse the attack and release parameters!
  97:         slewLimiter[ch].setParameters (releaseParam->getCurrentValue(), attackParam->getCurrentValue());
  98:         for (size_t k = 0; k < (size_t) numSamples; ++k)
  99:             compGainVec[k] = jmin (compGainVec[k], slewLimiter[ch].processSample (compGainVec[k]));
 100: 
 101:         FloatVectorOperations::multiply (x, compGainVec.data(), numSamples);
 102:     }
 103: 
 104:     oversample->processSamplesDown (block);
 105: 
 106:     bypass.processBlockOut (buffer, bypass.toBool (onOff));
 107: }
 108: 
```

## 3. The core tape model: hysteresis

This is the heart of the plugin. `HysteresisProcessor` does several things around the actual differential-equation solve:

- chooses a solver (`RK2`, `RK4`, Newton-Raphson variants, or `STN`)
- smooths parameter changes over time
- clips the incoming drive to keep the numerical solve stable
- oversamples before the nonlinear solve
- optionally runs a legacy "V1" mode that injects a high-frequency bias sinusoid
- applies post-hysteresis makeup gain and a DC blocker

The per-sample solve itself lives one level deeper in `HysteresisProcessing`, where the code computes a field derivative and advances the magnetization state `M` with the selected numerical method.

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Hysteresis/HysteresisProcessor.cpp 'void HysteresisProcessor::processBlock' 'template <typename T, typename SmoothType>'
```

```cpp
Plugin/Source/Processors/Hysteresis/HysteresisProcessor.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
 200: void HysteresisProcessor::processBlock (AudioBuffer<float>& buffer)
 201: {
 202:     const auto numChannels = buffer.getNumChannels();
 203: 
 204:     if (! bypass.processBlockIn (buffer, bypass.toBool (onOffParam)))
 205:         return;
 206: 
 207:     setSolver ((int) *modeParam);
 208:     setDrive (*driveParam);
 209:     setSaturation (*satParam);
 210:     setWidth (1.0f - *widthParam);
 211:     makeup.setTargetValue (calcMakeup());
 212:     setOversampling();
 213: 
 214:     bool needsSmoothing = drive[0].isSmoothing() || width[0].isSmoothing() || sat[0].isSmoothing() || wasV1 != useV1;
 215: 
 216:     if (useV1 != wasV1)
 217:     {
 218:         for (auto& hProc : hProcs)
 219:             hProc.reset();
 220:     }
 221: 
 222:     wasV1 = useV1;
 223: 
 224:     // clip input to avoid unstable hysteresis
 225:     for (int ch = 0; ch < numChannels; ++ch)
 226:     {
 227:         auto* bufferPtr = buffer.getWritePointer (ch);
 228:         FloatVectorOperations::clip (bufferPtr,
 229:                                      bufferPtr,
 230:                                      -clipLevel,
 231:                                      clipLevel,
 232:                                      buffer.getNumSamples());
 233:     }
 234: 
 235:     doubleBuffer.makeCopyOf (buffer, true);
 236: 
 237:     dsp::AudioBlock<double> block (doubleBuffer);
 238:     dsp::AudioBlock<double> osBlock = osManager.processSamplesUp (block);
 239: 
 240: #if HYSTERESIS_USE_SIMD
 241:     const auto n = osBlock.getNumSamples();
 242:     auto* inout = channelPointers.data();
 243:     const auto numChannelsPadded = channelPointers.size();
 244:     for (size_t ch = 0; ch < numChannelsPadded; ++ch)
 245:         inout[ch] = (ch < osBlock.getNumChannels() ? const_cast<double*> (osBlock.getChannelPointer (ch)) : zeroBlock.getChannelPointer (ch % Vec2::size));
 246: 
 247:     // interleave channels
 248:     for (size_t ch = 0; ch < numChannelsPadded; ch += Vec2::size)
 249:     {
 250:         auto* simdBlockData = reinterpret_cast<double*> (interleavedBlock.getChannelPointer (ch / Vec2::size));
 251:         interleaveSamples (&inout[ch], simdBlockData, static_cast<int> (n), static_cast<int> (Vec2::size));
 252:     }
 253: 
 254:     auto&& processBlock = interleavedBlock.getSubBlock (0, n);
 255: 
 256:     using ProcessType = Vec2;
 257: #else
 258:     auto&& processBlock = osBlock;
 259: 
 260:     using ProcessType = double;
 261: #endif
 262: 
 263:     if (useV1)
 264:     {
 265:         if (needsSmoothing)
 266:             processSmoothV1<ProcessType> (processBlock);
 267:         else
 268:             processV1<ProcessType> (processBlock);
 269:     }
 270:     else
 271:     {
 272:         switch (solver)
 273:         {
 274:             case RK2:
 275:                 if (needsSmoothing)
 276:                     processSmooth<RK2, ProcessType> (processBlock);
 277:                 else
 278:                     process<RK2, ProcessType> (processBlock);
 279:                 break;
 280:             case RK4:
 281:                 if (needsSmoothing)
 282:                     processSmooth<RK4, ProcessType> (processBlock);
 283:                 else
 284:                     process<RK4, ProcessType> (processBlock);
 285:                 break;
 286:             case NR4:
 287:                 if (needsSmoothing)
 288:                     processSmooth<NR4, ProcessType> (processBlock);
 289:                 else
 290:                     process<NR4, ProcessType> (processBlock);
 291:                 break;
 292:             case NR8:
 293:                 if (needsSmoothing)
 294:                     processSmooth<NR8, ProcessType> (processBlock);
 295:                 else
 296:                     process<NR8, ProcessType> (processBlock);
 297:                 break;
 298:             case STN:
 299:                 if (needsSmoothing)
 300:                     processSmooth<STN, ProcessType> (processBlock);
 301:                 else
 302:                     process<STN, ProcessType> (processBlock);
 303:                 break;
 304:             default:
 305:                 jassertfalse; // unknown solver!
 306:         };
 307:     }
 308: 
 309: #if HYSTERESIS_USE_SIMD
 310:     // de-interleave channels
 311:     for (size_t ch = 0; ch < numChannelsPadded; ch += Vec2::size)
 312:     {
 313:         auto* simdBlockData = reinterpret_cast<double*> (interleavedBlock.getChannelPointer (ch / Vec2::size));
 314:         deinterleaveSamples (simdBlockData,
 315:                              const_cast<double**> (&inout[ch]),
 316:                              static_cast<int> (n),
 317:                              static_cast<int> (Vec2::size));
 318:     }
 319: #endif
 320: 
 321:     osManager.processSamplesDown (block);
 322: 
 323:     buffer.makeCopyOf (doubleBuffer, true);
 324:     applyDCBlockers (buffer);
 325: 
 326:     bypass.processBlockOut (buffer, bypass.toBool (onOffParam));
 327: }
 328: 
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Hysteresis/HysteresisProcessing.h 'enum SolverType' 'private:'
```

```cpp
Plugin/Source/Processors/Hysteresis/HysteresisProcessing.h @ 604372e4ffd9690c3e283362e4598cb43edbb475
   7: enum SolverType
   8: {
   9:     RK2 = 0,
  10:     RK4,
  11:     NR4,
  12:     NR8,
  13:     STN,
  14:     NUM_SOLVERS
  15: };
  16: 
  17: /*
  18:     Hysteresis processing for a model of an analog tape machine.
  19:     For more information on the DSP happening here, see:
  20:     https://ccrma.stanford.edu/~jatin/420/tape/TapeModel_DAFx.pdf
  21: */
  22: class HysteresisProcessing
  23: {
  24: public:
  25:     HysteresisProcessing();
  26:     HysteresisProcessing (HysteresisProcessing&&) noexcept = default;
  27: 
  28:     void reset();
  29:     void setSampleRate (double newSR);
  30: 
  31:     void cook (double drive, double width, double sat, bool v1);
  32: 
  33:     /* Process a single sample */
  34:     template <SolverType solver, typename Float>
  35:     inline Float process (Float H) noexcept
  36:     {
  37:         auto H_d = HysteresisOps::deriv (H, H_n1, H_d_n1, (Float) T);
  38: 
  39:         Float M;
  40:         switch (solver)
  41:         {
  42:             case RK2:
  43:                 M = RK2Solver (H, H_d);
  44:                 break;
  45:             case RK4:
  46:                 M = RK4Solver (H, H_d);
  47:                 break;
  48:             case NR4:
  49:                 M = NRSolver<4> (H, H_d);
  50:                 break;
  51:             case NR8:
  52:                 M = NRSolver<8> (H, H_d);
  53:                 break;
  54:             case STN:
  55:                 M = STNSolver (H, H_d);
  56:                 break;
  57: 
  58:             default:
  59:                 M = 0.0;
  60:         };
  61: 
  62:                 // check for instability
  63: #if HYSTERESIS_USE_SIMD
  64:         auto notIllCondition = ! (xsimd::isnan (M) || (M > upperLim));
  65:         M = xsimd::select (notIllCondition, M, (Float) 0.0);
  66:         H_d = xsimd::select (notIllCondition, H_d, (Float) 0.0);
  67: #else
  68:         bool illCondition = std::isnan (M) || M > upperLim;
  69:         M = illCondition ? 0.0 : M;
  70:         H_d = illCondition ? 0.0 : H_d;
  71: #endif
  72: 
  73:         M_n1 = M;
  74:         H_n1 = H;
  75:         H_d_n1 = H_d;
  76: 
  77:         return M;
  78:     }
  79: 
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Hysteresis/HysteresisSTN.h 'class HysteresisSTN' '__EOF__'
```

```cpp
Plugin/Source/Processors/Hysteresis/HysteresisSTN.h @ 604372e4ffd9690c3e283362e4598cb43edbb475
  15: class HysteresisSTN
  16: {
  17: public:
  18:     HysteresisSTN();
  19:     HysteresisSTN (HysteresisSTN&&) noexcept = default;
  20: 
  21:     static constexpr size_t inputSize = 5;
  22:     static constexpr double diffMakeup = 1.0 / 6.0e4;
  23: 
  24:     void prepare (double sampleRate);
  25:     void setParams (float saturation, float width);
  26: 
  27:     inline double process (const double* input) noexcept
  28:     {
  29:         return stnModels[widthIdx][satIdx].forward (input) * sampleRateCorr;
  30:     }
  31: 
  32:     enum
  33:     {
  34:         numWidthModels = 11,
  35:         numSatModels = 21
  36:     };
  37: 
  38: private:
  39:     STNSpace::STNModel stnModels[numWidthModels][numSatModels];
  40:     double sampleRateCorr = 1.0;
  41:     size_t widthIdx = 0;
  42:     size_t satIdx = 0;
  43: 
  44:     JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR (HysteresisSTN)
  45: };
  46: 
  47: #endif // HYSTERESISSTN_H_INCLUDED
```

The `STN` option is especially interesting: instead of a classical numerical integrator, it uses a **State Transition Network** (a small neural network) as a learned solver for the hysteresis state update. In audio terms, the plugin is still trying to compute the next magnetization state from the previous state and the current field; it just swaps in a learned transition function for that step.

Also note the structure of `ToneControl`: it boosts/cuts before hysteresis, then applies the inverse move after hysteresis. That is analogous to using pre/de-emphasis around a nonlinear stage so the saturation character changes without leaving the EQ permanently tilted.

## 4. Damage and motion artifacts after the core tape stage

After the main magnetization model, the plugin layers on additional tape-machine imperfections:

- **Chew**: intermittent crinkling / dropout behavior
- **Degrade**: hiss/noise plus low-pass and gain variability
- **Wow & flutter**: low-rate and high-rate speed modulation implemented as a modulated delay line

These are conceptually separate from hysteresis. They are “what the machine and medium do around the magnetic process,” not the magnetization law itself.

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Chew/ChewProcessor.cpp 'void ChewProcessor::processShortBlock' '__EOF__'
```

```cpp
Plugin/Source/Processors/Chew/ChewProcessor.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
  75: void ChewProcessor::processShortBlock (AudioBuffer<float>& buffer)
  76: {
  77:     const float highFreq = jmin (22000.0f, 0.49f * sampleRate);
  78:     const float freqChange = highFreq - 5000.0f;
  79: 
  80:     if (*freq == 0.0f)
  81:     {
  82:         mix = 0.0f;
  83:         for (auto& filter : filt)
  84:             filter.setFreq (highFreq);
  85:     }
  86:     else if (*freq == 1.0f)
  87:     {
  88:         mix = 1.0f;
  89:         power = 3.0f * *depth;
  90:         const auto filterFreq = highFreq - freqChange * *depth;
  91:         for (auto& filter : filt)
  92:             filter.setFreq (filterFreq);
  93:     }
  94:     else if (sampleCounter >= samplesUntilChange)
  95:     {
  96:         sampleCounter = 0;
  97:         isCrinkled = ! isCrinkled;
  98: 
  99:         if (isCrinkled) // start crinkle
 100:         {
 101:             mix = 1.0f;
 102:             power = (1.0f + 2.0f * random.nextFloat()) * *depth;
 103:             const auto filterFreq = highFreq - freqChange * *depth;
 104:             for (auto& filter : filt)
 105:                 filter.setFreq (filterFreq);
 106: 
 107:             samplesUntilChange = getWetTime();
 108:         }
 109:         else // end crinkle
 110:         {
 111:             mix = 0.0f;
 112:             for (auto& filter : filt)
 113:                 filter.setFreq (highFreq);
 114:             samplesUntilChange = getDryTime();
 115:         }
 116:     }
 117:     else
 118:     {
 119:         power = (1.0f + 2.0f * random.nextFloat()) * *depth;
 120:         if (isCrinkled)
 121:         {
 122:             const auto filterFreq = highFreq - freqChange * *depth;
 123:             for (auto& filter : filt)
 124:                 filter.setFreq (filterFreq);
 125:         }
 126:     }
 127: 
 128:     dropout.setMix (mix);
 129:     dropout.setPower (1.0f + power);
 130: 
 131:     dropout.process (buffer);
 132:     for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
 133:         filt[ch].process (buffer.getWritePointer (ch), buffer.getNumSamples());
 134: 
 135:     sampleCounter += buffer.getNumSamples();
 136: }
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Degrade/DegradeProcessor.cpp 'void DegradeProcessor::cookParams' 'void DegradeProcessor::prepareToPlay'
```

```cpp
Plugin/Source/Processors/Degrade/DegradeProcessor.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
  25: void DegradeProcessor::cookParams()
  26: {
  27:     auto point1x = static_cast<bool> (point1xParam->load());
  28:     auto depthValue = point1x ? depthParam->getCurrentValue() * 0.1f : depthParam->getCurrentValue();
  29: 
  30:     float freqHz = 200.0f * powf (20000.0f / 200.0f, 1.0f - *amtParam);
  31:     float gainDB = -24.0f * depthValue;
  32: 
  33:     for (auto& noise : noiseProc)
  34:         noise.setGain (0.5f * depthValue * *amtParam);
  35: 
  36:     for (auto& filter : filterProc)
  37:         filter.setFreq (jmin (freqHz + (*varParam * (freqHz / 0.6f) * (random.nextFloat() - 0.5f)), 0.49f * fs));
  38: 
  39:     auto envSkew = 1.0f - std::pow (envParam->getCurrentValue(), 0.8f);
  40:     levelDetector.setParameters (10.0f, 20.0f * std::pow (5000.0f / 20.0f, envSkew));
  41:     gainProc.setGain (Decibels::decibelsToGain (jmin (gainDB + (*varParam * 36.0f * (random.nextFloat() - 0.5f)), 3.0f)));
  42: }
  43: 
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Degrade/DegradeProcessor.cpp 'void DegradeProcessor::processShortBlock' '__EOF__'
```

```cpp
Plugin/Source/Processors/Degrade/DegradeProcessor.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
  82: void DegradeProcessor::processShortBlock (AudioBuffer<float>& buffer)
  83: {
  84:     if (! bypass.processBlockIn (buffer, bypass.toBool (onOffParam)))
  85:         return;
  86: 
  87:     const auto numChannels = buffer.getNumChannels();
  88:     const auto numSamples = buffer.getNumSamples();
  89: 
  90:     sampleCounter += numSamples;
  91:     if (sampleCounter >= smallBlockSize)
  92:     {
  93:         cookParams();
  94:         sampleCounter = 0;
  95:     }
  96: 
  97:     noiseBuffer.setSize (numChannels, numSamples, false, false, true);
  98:     noiseBuffer.clear();
  99: 
 100:     dsp::AudioBlock<float> block (buffer);
 101:     dsp::AudioBlock<float> levelBlock (levelBuffer.getArrayOfWritePointers(), 1, numSamples);
 102:     dsp::ProcessContextNonReplacing<float> levelContext (block, levelBlock);
 103:     levelDetector.process (levelContext);
 104:     const auto* levelPtr = levelBuffer.getReadPointer (0);
 105: 
 106:     const auto applyEnvelope = envParam->getCurrentValue() > 0.0f;
 107:     for (int ch = 0; ch < numChannels; ++ch)
 108:     {
 109:         auto* noisePtr = noiseBuffer.getWritePointer (ch);
 110:         noiseProc[(size_t) ch].processBlock (noisePtr, numSamples);
 111: 
 112:         if (applyEnvelope)
 113:             FloatVectorOperations::multiply (noisePtr, levelPtr, numSamples);
 114: 
 115:         auto* xPtr = buffer.getWritePointer (ch);
 116:         FloatVectorOperations::add (xPtr, noisePtr, numSamples);
 117: 
 118:         filterProc[(size_t) ch].process (xPtr, numSamples);
 119:     }
 120: 
 121:     gainProc.processBlock (buffer);
 122:     bypass.processBlockOut (buffer, bypass.toBool (onOffParam));
 123: }
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Timing_Effects/WowFlutterProcessor.cpp 'void WowFlutterProcessor::processBlock' 'void WowFlutterProcessor::processWetBuffer'
```

```cpp
Plugin/Source/Processors/Timing_Effects/WowFlutterProcessor.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
  56: void WowFlutterProcessor::processBlock (AudioBuffer<float>& buffer)
  57: {
  58:     ScopedNoDenormals noDenormals;
  59: 
  60:     const auto numChannels = buffer.getNumChannels();
  61:     const auto numSamples = buffer.getNumSamples();
  62: 
  63:     auto curDepthWow = powf (*wowDepth, 3.0f);
  64:     auto wowFreq = powf (4.5, *wowRate) - 1.0f;
  65:     wowProcessor.prepareBlock (curDepthWow, wowFreq, wowVariance->getCurrentValue(), wowDrift->getCurrentValue(), numSamples, numChannels);
  66: 
  67:     auto curDepthFlutter = powf (powf (*flutterDepth, 3.0f) * 81.0f / 625.0f, 0.5f);
  68:     auto flutterFreq = 0.1f * powf (1000.0f, *flutterRate);
  69:     flutterProcessor.prepareBlock (curDepthFlutter, flutterFreq, numSamples, numChannels);
  70: 
  71:     bool shouldTurnOff = ! bypass.toBool (flutterOnOff) || (wowProcessor.shouldTurnOff() && flutterProcessor.shouldTurnOff());
  72:     if (bypass.processBlockIn (buffer, ! shouldTurnOff))
  73:     {
  74:         processWetBuffer (buffer);
  75: 
  76:         for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
  77:             dcBlocker[ch].processBlock (buffer.getWritePointer (ch), buffer.getNumSamples());
  78: 
  79:         bypass.processBlockOut (buffer, ! shouldTurnOff);
  80:     }
  81:     else
  82:     {
  83:         processBypassed (buffer);
  84:     }
  85: 
  86:     wowProcessor.plotBuffer (wowPlot);
  87:     flutterProcessor.plotBuffer (flutterPlot);
  88: }
  89: 
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Timing_Effects/WowFlutterProcessor.cpp 'void WowFlutterProcessor::processWetBuffer' 'void WowFlutterProcessor::processBypassed'
```

```cpp
Plugin/Source/Processors/Timing_Effects/WowFlutterProcessor.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
  90: void WowFlutterProcessor::processWetBuffer (AudioBuffer<float>& buffer)
  91: {
  92:     for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
  93:     {
  94:         auto* x = buffer.getWritePointer (ch);
  95:         for (int n = 0; n < buffer.getNumSamples(); ++n)
  96:         {
  97:             auto [wowLFO, wowOffset] = wowProcessor.getLFO (n, ch);
  98:             auto [flutterLFO, flutterOffset] = flutterProcessor.getLFO (n, ch);
  99: 
 100:             auto newLength = (wowLFO + flutterLFO + flutterOffset + wowOffset) * fs / 1000.0f;
 101:             newLength = jlimit (0.0f, (float) HISTORY_SIZE, newLength);
 102: 
 103:             delay.setDelay (newLength);
 104:             delay.pushSample (ch, x[n]);
 105:             x[n] = delay.popSample (ch);
 106:         }
 107: 
 108:         wowProcessor.boundPhase (ch);
 109:         flutterProcessor.boundPhase (ch);
 110:     }
 111: }
 112: 
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Timing_Effects/WowProcess.h 'inline std::pair<float, float> getLFO' 'inline void boundPhase'
```

```cpp
Plugin/Source/Processors/Timing_Effects/WowProcess.h @ 604372e4ffd9690c3e283362e4598cb43edbb475
  20:     inline std::pair<float, float> getLFO (int n, size_t ch) noexcept
  21:     {
  22:         updatePhase (ch);
  23:         auto curDepth = depthSlew[ch].getNextValue() * amp;
  24:         wowPtrs[ch][n] = curDepth * (std::cos (phase[ch]) + ohProc.process (n, ch));
  25:         return std::make_pair (wowPtrs[ch][n], curDepth);
  26:     }
  27: 
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Timing_Effects/FlutterProcess.h 'inline std::pair<float, float> getLFO' 'inline void boundPhase'
```

```cpp
Plugin/Source/Processors/Timing_Effects/FlutterProcess.h @ 604372e4ffd9690c3e283362e4598cb43edbb475
  23:     inline std::pair<float, float> getLFO (int n, size_t ch) noexcept
  24:     {
  25:         updatePhase (ch);
  26:         flutterPtrs[ch][n] = depthSlew[ch].getNextValue()
  27:                              * (amp1 * std::cos (phase1[ch] + phaseOff1)
  28:                                 + amp2 * std::cos (phase2[ch] + phaseOff2)
  29:                                 + amp3 * std::cos (phase3[ch] + phaseOff3));
  30:         return std::make_pair (flutterPtrs[ch][n], dcOffset);
  31:     }
  32: 
```

The wow/flutter block is worth translating into DSP language:

- `WowProcess` generates a **slow, wandering modulation** using a cosine plus an Ornstein-Uhlenbeck random process.
- `FlutterProcess` generates a **faster, more periodic modulation** by summing three sinusoids with fixed phase offsets.
- `WowFlutterProcessor` converts both modulation signals into **time-varying delay lengths in milliseconds**, then reads the audio through that modulated delay line.

That means the code is modeling speed instability as **time-base modulation**, not as amplitude modulation or pitch shifting by resynthesis.

## 5. Playback losses and stereo head alignment

The last major wet-path stage is `LossFilter`. This is the playback-head side of the model: spacing loss, thickness loss, gap loss, plus a resonant “head bump” EQ. These parameters are tied to physical dimensions like tape speed, tape spacing, tape thickness, and playback-head gap.

After that, `AzimuthProc` adds a stereo inter-channel delay difference that represents a playback head not being perfectly aligned relative to the tape path.

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Loss_Effects/LossFilter.cpp 'void LossFilter::calcCoefs' 'void LossFilter::processBlock'
```

```cpp
Plugin/Source/Processors/Loss_Effects/LossFilter.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
  70: void LossFilter::calcCoefs (MultiChannelIIR& filter)
  71: {
  72:     // Set freq domain multipliers
  73:     binWidth = fs / (float) curOrder;
  74:     auto H = Hcoefs.getRawDataPointer();
  75:     for (int k = 0; k < curOrder / 2; k++)
  76:     {
  77:         const auto freq = (float) k * binWidth;
  78:         const auto waveNumber = MathConstants<float>::twoPi * jmax (freq, 20.0f) / (*speed * 0.0254f);
  79:         const auto thickTimesK = waveNumber * (*thickness * (float) 1.0e-6);
  80:         const auto kGapOverTwo = waveNumber * (*gap * (float) 1.0e-6) / 2.0f;
  81: 
  82:         H[k] = expf (-waveNumber * (*spacing * (float) 1.0e-6)); // Spacing loss
  83:         H[k] *= (1.0f - expf (-thickTimesK)) / thickTimesK; // Thickness loss
  84:         H[k] *= sinf (kGapOverTwo) / kGapOverTwo; // Gap loss
  85:         H[curOrder - k - 1] = H[k];
  86:     }
  87: 
  88:     // Create time domain filter signal
  89:     auto h = currentCoefs.getRawDataPointer();
  90:     for (int n = 0; n < curOrder / 2; n++)
  91:     {
  92:         const auto idx = (size_t) curOrder / 2 + (size_t) n;
  93:         for (int k = 0; k < curOrder; k++)
  94:             h[idx] += Hcoefs[k] * cosf (MathConstants<float>::twoPi * (float) k * (float) n / (float) curOrder);
  95: 
  96:         h[idx] /= (float) curOrder;
  97:         h[curOrder / 2 - n] = h[idx];
  98:     }
  99: 
 100:     // compute head bump filters
 101:     calcHeadBumpFilter (*speed, *gap * (float) 1.0e-6, (double) fs, filter);
 102: }
 103: 
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Loss_Effects/LossFilter.cpp 'void LossFilter::processBlock' '__EOF__'
```

```cpp
Plugin/Source/Processors/Loss_Effects/LossFilter.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
 104: void LossFilter::processBlock (AudioBuffer<float>& buffer)
 105: {
 106:     const auto numChannels = buffer.getNumChannels();
 107:     const auto numSamples = buffer.getNumSamples();
 108: 
 109:     if (! bypass.processBlockIn (buffer, bypass.toBool (onOff)))
 110:         return;
 111: 
 112:     if ((*speed != prevSpeed || *spacing != prevSpacing || *thickness != prevThickness || *gap != prevGap) && fadeCount == 0)
 113:     {
 114:         calcCoefs (bumpFilter[! activeFilter]);
 115:         filters[! activeFilter].setCoefficients (currentCoefs.getRawDataPointer());
 116: 
 117:         bumpFilter[! activeFilter].reset();
 118: 
 119:         fadeCount = fadeLength;
 120:         prevSpeed = *speed;
 121:         prevSpacing = *spacing;
 122:         prevThickness = *thickness;
 123:         prevGap = *gap;
 124:     }
 125: 
 126:     if (fadeCount > 0)
 127:         fadeBuffer.makeCopyOf (buffer, true);
 128:     else
 129:         filters[! activeFilter].processBlockBypassed (buffer);
 130: 
 131:     // normal processing here...
 132:     {
 133:         dsp::AudioBlock<float> block (buffer);
 134:         filters[activeFilter].processBlock (buffer);
 135: 
 136:         bumpFilter[activeFilter].process (dsp::ProcessContextReplacing<float> { block });
 137:     }
 138: 
 139:     if (fadeCount > 0)
 140:     {
 141:         dsp::AudioBlock<float> fadeBlock (fadeBuffer);
 142:         filters[! activeFilter].processBlock (fadeBuffer);
 143: 
 144:         bumpFilter[! activeFilter].process (dsp::ProcessContextReplacing<float> { fadeBlock });
 145: 
 146:         // fade between buffers
 147:         auto startGain = (float) fadeCount / (float) fadeLength;
 148:         auto samplesToFade = jmin (fadeCount, numSamples);
 149:         fadeCount -= samplesToFade;
 150:         auto endGain = (float) fadeCount / (float) fadeLength;
 151: 
 152:         buffer.applyGainRamp (0, samplesToFade, startGain, endGain);
 153:         buffer.applyGain (samplesToFade, numSamples - samplesToFade, endGain);
 154: 
 155:         for (int ch = 0; ch < numChannels; ++ch)
 156:             buffer.addFromWithRamp (ch, 0, fadeBuffer.getReadPointer (ch), samplesToFade, 1.0f - startGain, 1.0f - endGain);
 157: 
 158:         if (fadeCount == 0)
 159:             activeFilter = ! activeFilter;
 160:     }
 161: 
 162:     azimuthProc.setAzimuthAngle (azimuth->getCurrentValue(), speed->getCurrentValue());
 163:     azimuthProc.processBlock (buffer);
 164: 
 165:     bypass.processBlockOut (buffer, bypass.toBool (onOff));
 166: }
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py snippet Plugin/Source/Processors/Loss_Effects/AzimuthProc.cpp 'void AzimuthProc::setAzimuthAngle' '__EOF__'
```

```cpp
Plugin/Source/Processors/Loss_Effects/AzimuthProc.cpp @ 604372e4ffd9690c3e283362e4598cb43edbb475
  31: void AzimuthProc::setAzimuthAngle (float angleDeg, float tapeSpeedIps)
  32: {
  33:     const auto delayIdx = size_t (angleDeg < 0.0f);
  34:     const auto tapeSpeed = inches2meters (tapeSpeedIps);
  35:     const auto azimuthAngle = deg2rad (std::abs (angleDeg));
  36: 
  37:     auto delayDist = tapeWidth * std::sin (azimuthAngle);
  38:     auto delaySamp = (delayDist * tapeSpeed) * fs;
  39: 
  40:     delaySampSmooth[delayIdx].setTargetValue (delaySamp);
  41:     delaySampSmooth[1 - delayIdx].setTargetValue (0.0f);
  42: }
  43: 
  44: void AzimuthProc::processBlock (AudioBuffer<float>& buffer)
  45: {
  46:     if (buffer.getNumChannels() != 2) // needs to be stereo!
  47:         return;
  48: 
  49:     for (int ch = 0; ch < buffer.getNumChannels(); ++ch)
  50:     {
  51:         auto* x = buffer.getWritePointer (ch);
  52:         if (delaySampSmooth[ch].isSmoothing())
  53:         {
  54:             for (int n = 0; n < buffer.getNumSamples(); ++n)
  55:             {
  56:                 delays[ch]->setDelay (delaySampSmooth[ch].getNextValue());
  57:                 delays[ch]->pushSample (0, x[n]);
  58:                 x[n] = delays[ch]->popSample (0);
  59:             }
  60:         }
  61:         else
  62:         {
  63:             for (int n = 0; n < buffer.getNumSamples(); ++n)
  64:             {
  65:                 delays[ch]->pushSample (0, x[n]);
  66:                 x[n] = delays[ch]->popSample (0);
  67:             }
  68:         }
  69:     }
  70: }
```

## 6. How the code lines up with the theory notes

The repository's own notes and paper line up closely with the code structure:

- the **continuous-time notes** define hysteresis and playback-head losses
- the paper has dedicated sections for **hysteresis**, **tape bias**, **wow and flutter**, and **oversampling**
- the real-time code mirrors that split: nonlinear magnetization, modulation, and playback losses are separate processors that are chained together in `processAudioBlock()`

So if you want to study the plugin in a linear way, the most faithful order is exactly the code path shown here: preconditioning → compression → hysteresis core → damage/motion artifacts → playback losses → dry/wet/output.

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py matches Notes/Continuous%20Time%20Considerations.md '^#|^##'
```

```cpp
Notes/Continuous%20Time%20Considerations.md @ 604372e4ffd9690c3e283362e4598cb43edbb475
   7: # Record head
  24: # Tape Magnetisation
  26: ## Deadzone
  36: ## Hysteresis
  48: # Playback head
  50: ## Ideal playback voltage
  62: ## Loss effects
  70: ### Spacing Loss
  76: ### Gap Loss
  82: ### Thickness Loss
  88: # Conclusion
```

```bash
python3 /home/runner/work/experiments/experiments/analog-tape-model-walkthrough/analog_tape_tools.py matches Paper/420_paper.tex '\\subsection\{Hysteresis\}|\\subsection\{Tape Bias\}|\\subsection\{Wow and Flutter\}|\\subsection\{Oversampling\}|\\subsection\{Play Head\}'
```

```cpp
Paper/420_paper.tex @ 604372e4ffd9690c3e283362e4598cb43edbb475
 255: \subsection{Play Head}
 318: \subsection{Hysteresis}
 409: \subsection{Play Head}
 515: \subsection{Tape Bias}
 543: \subsection{Wow and Flutter} \label{flutter}
 668: \subsection{Oversampling}
```

## Final mental model

If you only remember one thing, remember this:

> **CHOW Tape is not a single saturation block.** It is a chain that first conditions the signal, then runs a physically motivated hysteresis model, then layers in mechanical and playback artifacts, and only at the end recombines that wet path with a latency-aligned dry path.

For a DSP reader, the cleanest way to read the code is:

1. `PluginProcessor.cpp` for the block-level order
2. `InputFilters`, `MidSideProcessor`, and `ToneControl` for preconditioning
3. `CompressionProcessor` for dynamics before the core
4. `HysteresisProcessor` + `HysteresisProcessing` for the main nonlinear stateful solve
5. `Chew`, `Degrade`, and `WowFlutterProcessor` for defects and motion
6. `LossFilter` + `AzimuthProc` for playback-head coloration and stereo misalignment
7. `DryWetProcessor` + `latencyCompensation()` for final recombination
