# Shell/Bash Cheatsheet

``` bash
#!/bin/bash
```

## 1. FILE SYSTEM OPERATIONS

``` bash
# List files
ls -la          # List all files (including hidden) with details
ls -lh          # List with human-readable sizes

# Change directory
cd /path/to/dir # Go to directory
cd ..           # Go up one level
cd ~            # Go to home directory
cd -            # Go to previous directory

# Create directory
mkdir dir_name
mkdir -p a/b/c  # Create nested directories

# Copy
cp file1 file2  # Copy file
cp -r dir1 dir2 # Copy directory recursively

# Move / Rename
mv old_name new_name

# Remove
rm file         # Remove file
rm -r dir       # Remove directory recursively
rm -rf dir      # Force remove directory (careful!)
```

## 2. VIEWING & EDITING FILES

``` bash
# View content
cat file.txt
less file.txt   # View with pagination (q to quit)
head -n 10 file # View first 10 lines
tail -n 10 file # View last 10 lines
tail -f log.txt # Follow log file updates
```

## 3. SEARCHING & FINDING (GREP ENHANCED)

``` bash
# Grep (Global Regular Expression Print)
grep "pattern" file.txt        # Basic search
grep -r "pattern" dir/         # Recursive search in directory
grep -i "pattern" file.txt     # Case insensitive search
grep -v "pattern" file.txt     # Invert match (show lines NOT matching)
grep -l "pattern" dir/*        # List only filenames containing match
grep -L "pattern" dir/*        # List only filenames NOT containing match
grep -n "pattern" file.txt     # Show line numbers
grep -c "pattern" file.txt     # Count number of matches
grep -w "word" file.txt        # Match whole word only
grep -A 3 "pattern" file.txt   # Show 3 lines AFTER match
grep -B 3 "pattern" file.txt   # Show 3 lines BEFORE match
grep -C 3 "pattern" file.txt   # Show 3 lines CONTEXT (before & after)
grep -E "pat1|pat2" file.txt   # Extended regex (OR condition)

# Find (Search for files)
find /path -name "*.txt"       # Find files by name
find . -type f -size +10M      # Find files larger than 10MB
find . -mtime -7               # Find files modified in last 7 days
find . -name "*.log" -delete   # Find and delete files (careful!)
find . -name "*.py" -exec grep "import" {} + # Find files and grep inside them
```

## 4. TEXT PROCESSING (SED ENHANCED, AWK, CUT)

``` bash
# SED (Stream Editor)
sed 's/foo/bar/' file.txt      # Replace first 'foo' with 'bar' per line (prints to stdout)
sed 's/foo/bar/g' file.txt     # Replace ALL 'foo' with 'bar' per line
sed -i 's/foo/bar/g' file.txt  # In-place editing (modifies file directly)
sed -i.bak 's/foo/bar/g' file  # In-place editing with backup (file.txt.bak)
sed '/pattern/d' file.txt      # Delete lines matching pattern
sed -n '/pattern/p' file.txt   # Print ONLY lines matching pattern
sed '5,10d' file.txt           # Delete lines 5 through 10
sed -E 's/(ab)+/replaced/' file # Use extended regex

# AWK (Column processing)
awk '{print $1, $3}' file.txt  # Print specific columns
awk -F',' '{print $1}' file.csv # Specify delimiter (comma)
awk '$2 > 50 {print $0}' file  # Filter rows where col 2 > 50
awk '{sum+=$1} END {print sum}' file # Sum column 1

# CUT (Slice lines)
cut -d',' -f1 file.csv         # Cut by delimiter and take 1st field
cut -c1-5 file.txt             # Cut first 5 characters

# Sort & Uniq
sort file.txt | uniq           # Remove adjacent duplicates
sort file.txt | uniq -c        # Count occurrences
sort -n file.txt               # Numeric sort
sort -r file.txt               # Reverse sort
```

## 5. PERMISSIONS & OWNERSHIP

``` bash
# Change permissions
chmod 755 script.sh       # rwx for owner, rx for others
chmod +x script.sh        # Make executable

# Change owner
chown user:group file
chown -R user:group dir   # Recursive change
```

## 6. SYSTEM INFO & PROCESSES

``` bash
# Disk usage
df -h                     # Disk space usage
du -sh folder/            # Size of a directory

# Processes
ps aux                    # List all running processes
ps -ef | grep python      # Find python processes
top                       # Interactive process viewer
htop                      # Better interactive viewer

# Kill process
kill <pid>
kill -9 <pid>             # Force kill
killall <process_name>

# Memory
free -h
```

## 7. ARCHIVES & COMPRESSION

``` bash
# Tar
tar -czvf archive.tar.gz dir/  # Create compressed archive
tar -xzvf archive.tar.gz       # Extract archive

# Zip
zip -r archive.zip dir/        # Create zip
unzip archive.zip              # Extract zip
```

## 8. NETWORKING

``` bash
# Download files
wget http://example.com/file
curl -O http://example.com/file
curl -I http://example.com     # Fetch headers only

# Check connectivity
ping -c 4 google.com           # Ping 4 times

# Check ports/sockets
netstat -tulpn
ss -tulpn

# DNS lookup
nslookup google.com
dig google.com
```

## 9. DATABASES (POSTGRESQL - PSQL)

``` bash
# Connect to database
# psql -h <host> -p <port> -U <username> -d <dbname>
psql -h localhost -U postgres -d my_db

# Execute command and exit
psql -c "SELECT * FROM users;"

# Execute SQL file
psql -f schema.sql

# Useful Internal Commands (inside psql shell)
# \l        : List databases
# \c <db>   : Connect to database
# \dt       : List tables
# \d <table>: Describe table structure
# \du       : List users/roles
# \dn       : List schemas
# \q        : Quit psql

# Backup & Restore
pg_dump -U <user> <dbname> > backup.sql    # Backup
psql -U <user> <dbname> < backup.sql       # Restore
```

