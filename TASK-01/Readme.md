Terminal Hunt – Gargantua Challenge

This is how I solved the Gargantua part of Terminal Hunt.

---

1. Facility on Earth
I found a hidden folder called `.facility` in Earth → Russia → Vladimir_Oblast. 
Inside it was `gravity_equation.txt` which gave me a Base64 string (this was the first key).

Commands used:
bash
grep -Ri "facility" /home/manishj/Terminal-Hunt
ls -a
cd Earth/Russia/Vladimir_Oblast/.facility
ls
cat gravity_equation.txt
rm gravity_equation.txt
---

2. Wormhole near Saturn
Next I made the wormhole script executable and ran it. 
That gave me the second key, which was another Base64 string.

Commands used:
cd Earth/Saturn
chmod +x wormhole.sh
./wormhole.sh


---

3. Planets in Gargantua
The instructions said to look for files between 100–105 bytes. 
I checked all of them, but they were just decoys saying:
Nope. this planet can't support life


There was also one odd file with 103 null bytes, but it didn’t say anything about habitability. 
The real confirmation was in `Gargantua/HABITABLE.txt`, which is 127 bytes long. 
It clearly says:
Yes. This zone is habitable. Breathe easy...


So even though it didn’t match the 100–105 byte condition, this was the actual habitable planet.

Commands used:
find Gargantua -type f -size +100c -size -105c
cat Gargantua/HABITABLE.txt

---
4. Message from Them
Inside `Gargantua/the_centre/.the_core/` there was `.message_from_Them.txt`. 
It had binary data. 

- I converted the binary into ASCII → got a Base64 string. 
- I decoded the Base64 → the message was:  e, and add a screenshot to solutions.md.

So the message from Them was basically telling me to add proof to my solutions file.

---

5. The Singularity
In `Gargantua/the_centre/.the_singularity/` there was the script `gravity_singularity.sh`. 
This script checks a password against an environment variable called `LOCA_LOCA`.

I created `LOCA_LOCA` by putting together the three keys (facility, wormhole, habitable). 
Then I ran the script and typed in the same string. 

Commands used:
export LOCA_LOCA='T25lIGxhc3QgdGFzaywgYW5kIHlvdSdsbCBoYXZlIHN1Y2Nlc3NmdWxseSBjb21wbGV0ZWQgdGhlIFRlcm1pbmFsIEh1bnQhIFJ1biBncmF2aXR5Yes. This zone is habitable. Breathe easy...'

cd Gargantua/the_centre/.the_singularity
./gravity_singularity.sh
# then I pasted the same string when asked.


This unlocked the final page with the success message.

