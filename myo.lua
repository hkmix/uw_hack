scriptId = "com.jfoxcrof.enghack"

CTIME = 0
CDELAY = 1
INITIALIZE=0
YAW_CENTER=0
YAW_RIGHT=0
YAW_LEFT=0
PITCH_CENTER=0
PITCH_UP=0
PITCH_DOWN=0
INITIALIZE=0

function onForegroundWindowChange(app, title)
    myo.debug("onForegroundWindowChange: " .. app .. ", " .. title)
	if (title=="Rogue@UW - ENGHack 2014" or title=="Debug Console") then
		return true
	end
	return false
end

function onPoseEdge(pose, edge)
    myo.debug("onPoseEdge: " .. pose .. ", " .. edge)
	if (pose=="fingersSpread" and edge=="on") then
		if (INITIALIZE==0) then
			for i=0,10,1 do
				PITCH_CENTER=PITCH_CENTER+myo.getPitch()
				YAW_CENTER=YAW_CENTER+myo.getYaw()
			end
			PITCH_CENTER=PITCH_CENTER/10
			YAW_CENTER=YAW_CENTER/10+3
			INITIALIZE=1
		elseif (INITIALIZE==1) then
			for i=0,10,1 do
				PITCH_UP=PITCH_UP+myo.getPitch()
				YAW_RIGHT=YAW_RIGHT+myo.getYaw()
			end
			PITCH_UP=PITCH_UP/10
			YAW_RIGHT=YAW_RIGHT/10+3
			INITIALIZE=2
		elseif (INITIALIZE==2) then
			for i=0,10,1 do
				PITCH_DOWN=PITCH_DOWN+myo.getPitch()
				YAW_LEFT=YAW_LEFT+myo.getYaw()
			end
			PITCH_DOWN=PITCH_DOWN/10
			YAW_LEFT=YAW_LEFT/10+3
			INITIALIZE=3
		elseif (INITIALIZE==3) then
			myo.debug("\nPitch Up: "..PITCH_UP.."\nPitch Center: "..PITCH_CENTER.."\nPitch Down: "..PITCH_DOWN)
			myo.debug("\nYaw Right: "..YAW_RIGHT.."\nYaw Center: "..YAW_CENTER.."\nYaw Left: "..YAW_LEFT)
			myo.keyboard("comma", "press")
		end
	elseif (pose=="waveIn" and edge=="on") then
		myo.keyboard("return", "press")
	end
end

function onPeriodic()
	CTIME = CTIME + 1
    if (CTIME > CDELAY) then
		if(myo.getPitch() < PITCH_UP+math.abs((PITCH_UP+PITCH_CENTER)/2)/2) then
			myo.keyboard("up_arrow", "press")
			myo.debug("Up!")
		end
		if(myo.getPitch() > PITCH_DOWN-math.abs((PITCH_UP+PITCH_DOWN)/2)/2) then
			myo.keyboard("down_arrow", "press")
			myo.debug("Down!")
		end
		if(myo.getYaw()+3 < YAW_RIGHT) then
			myo.keyboard("right_arrow", "press")
			myo.debug("Right!")
		end
		if(myo.getYaw()+3 > YAW_LEFT) then
			myo.keyboard("left_arrow", "press")
			myo.debug("Left!")
		end
        CTIME = 0
    end
end