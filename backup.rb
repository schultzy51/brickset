require 'json'
require 'pry'
require 'configparser'
require 'optparse'
require 'brickset'

class Cache
  def initialize(config_file = '.config', delay = 10)
    config = ConfigParser.new(config_file)
    api_key = config.dig('brickset_account', 'api_key')

    @delay = delay
    Brickset.configure { |config| config.api_key = api_key }
    @brickset = Brickset::Api.new

    @data_dir = 'data'
    @sets_dir = 'sets'
    @years_dir = 'years'
    @subthemes_dir = 'subthemes'

    @themes_file_name = File.join(@data_dir, 'brickset_themes.json')
    @years_file_name = File.join(@data_dir, 'brickset_years.json')
    @recent_sets_file_name = File.join(@data_dir, 'brickset_recent_sets.json')

    prepare
  end

  def prepare
    dirs = [
        File.join(@data_dir),
        File.join(@data_dir, @sets_dir),
        File.join(@data_dir, @years_dir),
        File.join(@data_dir, @subthemes_dir)
    ]

    dirs.each { |dir| Dir.mkdir(dir) unless File.exists?(dir) }
  end

  def save_themes(filename, force = false)
    File.delete(filename) if File.exist?(filename) && force

    unless File.exist?(filename)
      puts filename

      sleep(@delay)

      raw_themes = @brickset.themes
      json_themes = raw_themes.map { |theme| JSON.generate(theme) }
      File.open(filename, 'w') { |file| file.puts(json_themes) }
    end
  end

  def load_themes(filename)
    lines = File.readlines(filename)
    data = lines.map { |line| JSON.parse(line, {symbolize_names: true}) }
    data.map { |datum| Brickset::Theme.new(datum) }
  end

  def themes
    save_themes(@themes_file_name)
    load_themes(@themes_file_name)
  end

  def save_theme_years(filename, theme, force = false)
    File.delete(filename) if File.exist?(filename) && force

    unless File.exist?(filename)
      puts filename

      sleep(@delay)

      raw_years = @brickset.years(theme.name)
      json_years = raw_years.map { |year| JSON.generate(year) }
      File.open(filename, 'w') { |file| file.puts(json_years) }
    end
  end

  def load_theme_years(filename)
    lines = File.readlines(filename)
    data = lines.map { |line| JSON.parse(line, {symbolize_names: true}) }
    data.map { |datum| Brickset::Year.new(datum) }
  end

  def years(themes)
    years = []
    themes.each do |theme|
      filename = data_filename(sub_dir: @years_dir, theme_name: theme.name)
      save_theme_years(filename, theme)
      years += load_theme_years(filename)
    end
    years
  end

  def save_theme_subthemes(filename, theme, force = false)
    File.delete(filename) if File.exist?(filename) && force

    unless File.exist?(filename)
      puts filename

      sleep(@delay)

      raw_subthemes = @brickset.subthemes(theme.name)
      json_subthemes = raw_subthemes.map { |subtheme| JSON.generate(subtheme) }
      File.open(filename, 'w') { |file| file.puts(json_subthemes) }
    end
  end

  def load_theme_subthemes(filename)
    lines = File.readlines(filename)
    data = lines.map { |line| JSON.parse(line, {symbolize_names: true}) }
    data.map { |datum| Brickset::Subtheme.new(datum) }
  end

  def subthemes(themes)
    subthemes = []
    themes.each do |theme|
      filename = data_filename(sub_dir: @subthemes_dir, theme_name: theme.name)
      save_theme_subthemes(filename, theme)
      subthemes += load_theme_subthemes(filename)
    end
    subthemes
  end

  def save_theme_sets(filename, theme, force = false)
    File.delete(filename) if File.exist?(filename) && force

    unless File.exist?(filename)
      puts filename

      page_number = 1
      page_size = 40
      raw_sets = []

      begin
        sleep(@delay)

        partial_raw_sets = @brickset.sets(theme: theme.name, page_size: page_size, page_number: page_number, order_by: 'YearFrom')

        count = partial_raw_sets.size
        page_number = page_number + 1

        puts count

        raw_sets += partial_raw_sets
      end while (count == page_size)

      json_sets = raw_sets.map { |set| JSON.generate(set) }
      File.open(filename, 'w') { |file| file.puts(json_sets) }
    end
  end

  def load_theme_sets(filename)
    lines = File.readlines(filename)
    data = lines.map { |line| JSON.parse(line, {symbolize_names: true}) }
    data.map { |datum| Brickset::Set.new(datum) }
  end

  def sets(themes)
    sets = []
    themes.each do |theme|
      filename = data_filename(sub_dir: @sets_dir, theme_name: theme.name)
      save_theme_sets(filename, theme)
      sets += load_theme_sets(filename)
    end
    sets
  end

  def save_recent_sets(filename, force = false)
    File.delete(filename) if File.exist?(filename) && force

    unless File.exist?(filename)
      puts filename

      sleep(@delay)

      raw_recent_sets = @brickset.recently_updated(60 * 24 * 14)
      json_recent_sets = raw_recent_sets.map { |set| JSON.generate(set) }
      File.open(filename, 'w') { |file| file.puts(json_recent_sets) }
    end
  end

  def load_recent_sets(filename)
    lines = File.readlines(filename)
    data = lines.map { |line| JSON.parse(line, {symbolize_names: true}) }
    data.map { |datum| Brickset::Set.new(datum) }
  end

  def recent_sets(force = false)
    save_recent_sets(@recent_sets_file_name, force = force)
    load_recent_sets(@recent_sets_file_name)
  end

  def check(themes, years, subthemes, sets, clean = false)
    mismatch = {
        set_mismatch: [],
        subtheme_mismatch: []
    }

    theme_set_count = themes.inject(0) { |result, element| result + element.set_count }
    subthemes_set_count = subthemes.inject(0) { |result, element| result + element.set_count }
    years_set_count = years.inject(0) { |result, element| result + element.set_count }
    sets_count = sets.count

    theme_subtheme_count = themes.inject(0) { |result, element| result + element.subtheme_count }
    subtheme_count = subthemes.count

    themes.each do |theme|
      filename = data_filename(sub_dir: @sets_dir, theme_name: theme.name)
      file_count = load_theme_sets(filename).count
      unless file_count == theme.set_count
        puts "SET MISMATCH (#{theme.name}): #{file_count} / #{theme.set_count}"
        mismatch[:set_mismatch] << filename
      end
    end

    themes.each do |theme|
      filename = data_filename(sub_dir: @subthemes_dir, theme_name: theme.name)
      subthemes = load_theme_subthemes(filename)
      file_count = subthemes.count - subthemes.select { |subtheme| subtheme.name == '{None}' }.count
      unless file_count == theme.subtheme_count
        puts "SUBTHEME MISMATCH (#{theme.name}): #{file_count} / #{theme.subtheme_count}"
        mismatch[:subtheme_mismatch] << filename
      end
    end

    puts "THEMES SET COUNT:      #{theme_set_count}"
    puts "YEARS SET COUNT:       #{years_set_count}"
    puts "SUBTHEMES SET COUNT:   #{subthemes_set_count}"
    puts "SET COUNT:             #{sets_count}"
    puts "THEMES SUBTHEME COUNT: #{theme_subtheme_count}"
    puts "SUBTHEME COUNT:        #{subtheme_count}"

    mismatch
  end

  private

  def data_filename(sub_dir: '', theme_name: '')
    name = 'brickset'
    name += "_#{sub_dir}" unless sub_dir.blank?
    name += "_#{theme_name}" unless theme_name.blank?
    File.join(@data_dir, sub_dir, "#{name.parameterize.underscore}.json")
  end
end

###########################################################################################

options = {
    verbose: false,
    recent: false
}
OptionParser.new do |opts|
  opts.banner = "Usage: backup.rb [options]"

  opts.on("-v", "--[no-]verbose", "Run verbosely") do |v|
    options[:verbose] = v
  end

  opts.on("-r", "--[no-]recent", "Pull recent") do |r|
    options[:recent] = r
  end
end.parse!

cache = Cache.new

themes = cache.themes
years = cache.years(themes)
subthemes = cache.subthemes(themes)
sets = cache.sets(themes)
puts cache.check(themes, years, subthemes, sets)

cache.recent_sets(force = options[:recent])

# config = ConfigParser.new('.config')
# api_key = config.dig('wanted_account', 'api_key')
# username = config.dig('wanted_account', 'username')
# password = config.dig('wanted_account', 'password')
#
# brickset = Brickset::Api.new(api_key)
#
# user_hash = brickset.login(username, password)
#
# sets = brickset.sets(user_hash: user_hash, wanted: 1, page_size: 50)
# sets.map! { |set| Brickset::Set.new(set) }
# sets.sort! do |a, b|
#   if a.released == b.released
#     if a.released # both released
#       if a.us_date_added_to_sah.nil? and b.us_date_added_to_sah.nil?
#         a.number <=> b.number
#       elsif a.us_date_added_to_sah and b.us_date_added_to_sah
#         a.us_date_added_to_sah <=> b.us_date_added_to_sah
#       elsif a.us_date_added_to_sah.nil?
#         1
#       else
#         -1
#       end
#     else
#       a.number <=> b.number
#     end
#   elsif a.released
#     -1
#   else
#     1
#   end
# end
#
# sets.each do |set|
#   puts "#{set.number}, #{set.name}, #{set.year}, #{set.us_date_added_to_sah}, #{set.us_date_removed_from_sah}"
# end
#
# collection_totals = brickset.collection_totals(user_hash).map { |ct| Brickset::CollectionTotals.new(ct) }
# minifig_collection = brickset.minifig_collection(user_hash).map { |mc| Brickset::MinifigCollection.new(mc) }
# themes_for_user = brickset.themes_for_user(user_hash).map { |t| Brickset::Theme.new(t) }
# subthemes_for_user = brickset.subthemes_for_user(user_hash, 'Star Wars').map { |s| Brickset::Subtheme.new(s) }
# years_for_user = brickset.years_for_user(user_hash, 'Star Wars').map { |y| Brickset::Year.new(y) }
